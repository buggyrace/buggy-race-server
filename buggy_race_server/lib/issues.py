import csv

class IssueParser:
    def __init__(self, issues_file):
        self.issues_file = issues_file

    def parse_issues(self):
        # If Github requires CRLF (which it seemed to do),
        # see config setting IS_ISSUES_CSV_CRLF_TERMINATED
        issues = []
        with open(self.issues_file) as issues_file:
            for row in csv.reader(issues_file):
                issues.append({
                    'title': row[0],
                    'body': row[1].replace("\\n", "\n")
                })

        return issues
