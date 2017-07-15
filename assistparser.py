import regex


__all__ = [
    "parse_section",
    "tokenize",
]


def parse_section(course_section):
    TO_lines, FROM_lines = _split_lines(course_section)
    return tokenize(TO_lines), tokenize(FROM_lines)


def _split_lines(raw_course_lines):
    TO_lines = []
    FROM_lines = []
    for line in raw_course_lines:
        to_part, from_part = line.split('|')
        TO_lines.append(to_part)
        FROM_lines.append(from_part)

    return TO_lines, FROM_lines


def tokenize(raw_course_line_halves):
    if tokenize.pattern is None:
        tokenize.pattern = regex.compile(
            r"""
            (?(DEFINE)
                (?<department_char>[A-Z&\d\/.])
                (?<title_char>[\w.,;:!\"\'&+-\/]
                             |(?!\(\d(?:\.\d)?\))[()])
                (?<title_words>(?&title_char)+(?:\ (?&title_char)+)*)
            )

            ^
            (?:(?<note>[*#@+%]+)\ *)?
            (?<department>(?&department_char)+(?:\ (?&department_char)+)*)
            \ 
            (?<cnum>[\dA-Z]+[A-Z]*)
            \ +
            (?<FROM_and>&)?
            \ +
            (?<title>(?&title_words))
            \ +
            \((?<units>\d(?:\.\d)?)\)
            $

            |^(?<FROM_or>\ {0,4}OR)
            |^(?<TO_or>\ {5,}OR)
            |^(?<TO_and>\ +AND\ +)


            |^(?<no_articulation>N[Oo][Tt]?\ )
              (?:[A-Za-z ]+[^A-Za-z \n]\ ?(?<two_line_no_articulation>[A-Z]))?

            |^(?<same_as>\ +Same\ as:)

            |^\ +(?<title_contd>\ (?&title_words))
            """,
            regex.VERBOSE
        )
        tokenize.special_info_pattern = regex.compile(r'\([A-Z\d]')
        tokenize.parenthesized_info_opening = regex.compile(r'^\([A-Z\d]')
        tokenize.parenthesized_info_closing = regex.compile(r'^[^)]+\) *$')
        tokenize.blank_line = regex.compile(r'^ *$')

    def num(x):
        try:
            return int(x)
        except ValueError:
            return float(x)

    tokens = []
    token = None
    processing_course = False
    processing_FROM_and = False
    processing_info_token = False
    processing_parenthesized_info = False
    processing_two_line_no_articulation = False

    for line in raw_course_line_halves:
        if processing_two_line_no_articulation:
            token['details'] += line.rstrip()
            tokens.append(token)
            processing_two_line_no_articulation = False
            continue

        match = tokenize.pattern.match(line)
        if match:
            if processing_info_token:
                token = {'info': token['info'].strip()}
                tokens.append(token)
                token = None
                processing_info_token = False

            if processing_course and not match.captures("title_contd"):
                processing_course = False
                tokens.append(token)
                token = None
                if processing_FROM_and:
                    tokens.append({'operator': '&'})
                    processing_FROM_and = False

            if match.captures("department"):
                token = {
                    "department": match.captures("department")[0],
                    "cnum": match.captures("cnum")[0],
                    "title": match.captures("title")[0],
                    "units": num(match.captures("units")[0])
                }
                processing_course = True
            elif match.captures("title_contd"):
                token["title"] += match.captures("title_contd")[0]

            elif match.captures("no_articulation"):
                if match.captures("two_line_no_articulation"):
                    details = line[match.start('two_line_no_articulation'):]
                    token = {'no-articulation': None, 'details': details}
                    processing_two_line_no_articulation = True
                else:
                    tokens.append({'no-articulation': None})

            if match.captures("FROM_and"):
                processing_FROM_and = True

            if match.captures("FROM_or"):
                tokens.append({'operator': 'FROM_or'})

            if match.captures("TO_or"):
                tokens.append({'operator': 'TO_or'})

            if match.captures("TO_and"):
                tokens.append({'operator': 'AND'})

            if match.captures("note"):
                assert processing_course
                token["note"] = match.captures("note")[0]

            if match.captures("same_as"):
                continue

        elif tokenize.blank_line.match(line):
            continue

        else:
            if processing_info_token:
                if tokenize.parenthesized_info_opening.match(line):
                    token = {'info': token['info'].strip()}
                    tokens.append(token)
                    token = {'info': line.strip() + ' '}
                    processing_parenthesized_info = True
                elif processing_parenthesized_info \
                and tokenize.parenthesized_info_closing.match(line):
                    token['info'] += line.strip()
                    tokens.append(token)
                    token = None
                    processing_parenthesized_info = False
                    processing_info_token = False
                else:
                    token['info'] += line.strip() + ' '
            else:
                if processing_course:
                    assert token is not None
                    tokens.append(token)
                    processing_course = False
                processing_FROM_and = False
                processing_info_token = True
                token = {'info': line.strip() + ' '}

    if token:
        tokens.append(token)

    return tokens

tokenize.pattern = None
tokenize.parenthesized_info_opening = None
tokenize.parenthesized_info_closing = None
tokenize.blank_line = None
