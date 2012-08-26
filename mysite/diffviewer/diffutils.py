import re

ALPHANUM_RE = re.compile(r'\w')
WHITESPACE_RE = re.compile(r'\s')

def is_valid_move_range(lines):
    """Determines if a move range is valid and should be included.

    This performs some tests to try to eliminate trivial changes that
    shouldn't have moves associated.

    Specifically, a move range is valid if it has at least one line
    with alpha-numeric characters and is at least 4 characters long when
    stripped.
    """
    for line in lines:
        line = line.strip()

        if len(line) >= 4 and ALPHANUM_RE.search(line):
            return True

    return False

def opcodes_with_metadata(differ):
    """Returns opcodes from the differ with extra metadata.

    This is a wrapper around a differ's get_opcodes function, which returns
    extra metadata along with each range. That metadata includes information
    on moved blocks of code and whitespace-only lines.

    This returns a list of opcodes as tuples in the form of
    (tag, i1, i2, j1, j2, meta).
    """
    groups = []
    removes = {}
    inserts = []

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        meta = {
            # True if this chunk is only whitespace.
            "whitespace_chunk": False,

            # List of tuples (x,y), with whitespace changes.
            "whitespace_lines": [],
        }

        if tag == 'replace':
            # replace groups are good for whitespace only changes.
            assert (i2 - i1) == (j2 - j1)

            for i, j in zip(xrange(i1, i2), xrange(j1, j2)):
                if (WHITESPACE_RE.sub("", differ.a[i]) ==
                    WHITESPACE_RE.sub("", differ.b[j])):
                    # Both original lines are equal when removing all
                    # whitespace, so include their original line number in
                    # the meta dict.
                    meta["whitespace_lines"].append((i + 1, j + 1))

            # If all lines are considered to have only whitespace change,
            # the whole chunk is considered a whitespace-only chunk.
            if len(meta["whitespace_lines"]) == (i2 - i1):
                meta["whitespace_chunk"] = True

        group = (tag, i1, i2, j1, j2, meta)
        groups.append(group)

        # Store delete/insert ranges for later lookup. We will be building
        # keys that in most cases will be unique for the particular block
        # of text being inserted/deleted. There is a chance of collision,
        # so we store a list of matching groups under that key.
        #
        # Later, we will loop through the keys and attempt to find insert
        # keys/groups that match remove keys/groups.
        if tag == 'delete':
            for i in xrange(i1, i2):
                line = differ.a[i].strip()

                if line:
                    removes.setdefault(line, []).append((i, group))
        elif tag == 'insert':
            inserts.append(group)

    # We now need to figure out all the moved locations.
    #
    # At this point, we know all the inserted groups, and all the individually
    # deleted lines. We'll be going through and finding consecutive groups
    # of matching inserts/deletes that represent a move block.
    #
    # The algorithm will be documented as we go in the code.
    #
    # We start by looping through all the inserted groups.
    for itag, ii1, ii2, ij1, ij2, imeta in inserts:
        # Store some state on the range we'll be working with inside this
        # insert group.
        #
        # i_move_cur is the current location inside the insert group
        # (from ij1 through ij2).
        #
        # i_move_range is the current range of consecutive lines that we'll
        # use for a move. Each line in this range has a corresponding
        # consecutive delete line.
        #
        # r_move_ranges represents deleted move ranges. The key is a
        # string in the form of "{i1}-{i2}-{j1}-{j2}", with those positions
        # taken from the remove group for the line. The value
        # is an array of tuples of (r_start, r_end, r_group). These values
        # are used to quickly locate deleted lines we've found that match
        # the inserted lines, so we can assemble ranges later.
        i_move_cur = ij1
        i_move_range = (i_move_cur, i_move_cur)
        r_move_ranges = {} # key -> [(start, end, group)]

        # Loop through every location from ij1 through ij2 until we've
        # reached the end.
        while i_move_cur <= ij2:
            try:
                iline = differ.b[i_move_cur].strip()
            except IndexError:
                iline = None

            if iline is not None and iline in removes:
                # The inserted line at this location has a corresponding
                # removed line.
                #
                # If there's already some information on removed line ranges
                # for this particular move block we're processing then we'll
                # update the range.
                #
                # The way we do that is to find each removed line that
                # matches this inserted line, and for each of those find
                # out if there's an existing move range that the found
                # removed line immediately follows. If there is, we update
                # the existing range.
                #
                # If there isn't any move information for this line, we'll
                # simply add it to the move ranges.
                for ri, rgroup in removes.get(iline, []):
                    key = "%s-%s-%s-%s" % rgroup[1:5]

                    if r_move_ranges:
                        for i, r_move_range in \
                            enumerate(r_move_ranges.get(key, [])):
                            # If the remove information for the line is next in
                            # the sequence for this calculated move range...
                            if ri == r_move_range[1] + 1:
                                r_move_ranges[key][i] = (r_move_range[0], ri,
                                                         rgroup)
                                break
                    else:
                        # We don't have any move ranges yet, so it's time to
                        # build one based on any removed lines we find that
                        # match the inserted line.
                        r_move_ranges[key] = [(ri, ri, rgroup)]

                # On to the next line in the sequence...
                i_move_cur += 1
            else:
                # We've reached the very end of the insert group. See if
                # we have anything that looks like a move.
                if r_move_ranges:
                    r_move_range = None

                    # Go through every range of lines we've found and
                    # find the longest.
                    #
                    # The longest move range wins. If we find two ranges that
                    # are equal, though, we'll ignore both. The idea is that
                    # if we have two identical moves, then it's probably
                    # common enough code that we don't want to show the move.
                    # An example might be some standard part of a comment
                    # block, with no real changes in content.
                    #
                    # Note that with the current approach, finding duplicate
                    # moves doesn't cause us to reset the winning range
                    # to the second-highest identical match. We may want to
                    # do that down the road, but it means additional state,
                    # and this is hopefully uncommon enough to not be a real
                    # problem.
                    for ranges in r_move_ranges.itervalues():
                        for r1, r2, rgroup in ranges:
                            if not r_move_range:
                                r_move_range = (r1, r2, rgroup)
                            else:
                                len1 = r_move_range[2] - r_move_range[1]
                                len2 = r2 - r1

                                if len1 < len2:
                                    r_move_range = (r1, r2, rgroup)
                                elif len1 == len2:
                                    # If there are two that are the same, it
                                    # may be common code that we don't want to
                                    # see moves for. Comments, for example.
                                    r_move_range = None

                    # If we have a move range, see if it's one we want to
                    # include or filter out. Some moves are not impressive
                    # enough to display. For example, a small portion of a
                    # comment, or whitespace-only changes.
                    if (r_move_range and
                        is_valid_move_range(
                            differ.a[r_move_range[0]:r_move_range[1]])):

                        # Rebuild the insert and remove ranges based on
                        # where we are now and which range we won.
                        #
                        # The new ranges will be actual lists of positions,
                        # rather than a beginning and end. These will be
                        # provided to the renderer.
                        #
                        # The ranges expected by the renderers are 1-based,
                        # whereas our calculations for this algorithm are
                        # 0-based, so we add 1 to the numbers.
                        #
                        # The upper boundaries passed to the range() function
                        # must actually be one higher than the value we want.
                        # So, for r_move_range, we actually increment by 2.
                        # We only increment i_move_cur by one, because
                        # i_move_cur already factored in the + 1 by being
                        # at the end of the while loop.
                        i_move_range = range(i_move_range[0] + 1,
                                             i_move_cur + 1)
                        r_move_range = range(r_move_range[0] + 1,
                                             r_move_range[1] + 2)

                        rmeta = rgroup[-1]
                        rmeta.setdefault('moved', {}).update(
                            dict(zip(r_move_range, i_move_range)))
                        imeta.setdefault('moved', {}).update(
                            dict(zip(i_move_range, r_move_range)))

                # Reset the state for the next range.
                i_move_cur += 1
                i_move_range = (i_move_cur, i_move_cur)
                r_move_ranges = {}

    return groups

