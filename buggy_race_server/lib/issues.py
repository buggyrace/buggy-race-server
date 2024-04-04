import csv

class IssueParser:
    def __init__(self, issues_file, header_row):
        self.issues_file = issues_file
        self.header_row = header_row

    def parse_issues(self):
        print(f"FIXME test DEBUG: self.header_row={self.header_row}")
        # If Github requires CRLF (which it seemed to do),
        # see config setting IS_ISSUES_CSV_CRLF_TERMINATED
        # Note: parse_issues currently ALWAYS produces issues with 'title' and
        #       'body' regardless of the header_row (which is currently only
        #       used when producing the CSV file)
        # in
        issues = []
        with open(self.issues_file) as issues_file:
            line_no = 0
            for line_no, row in enumerate(csv.reader(issues_file), start=0):
                if line_no == 0 and self.header_row:
                    pass # skip the header row
                else:
                    issues.append({
                        'title': row[0],
                        'body': row[1].replace("\\n", "\n")
                    })
        return issues
