import csv

class IssueParser:
    def __init__(self, issues_file):
        self.issues_file = issues_file

    def parse_issues(self):
        issues = []
        with open(self.issues_file) as issues_file:
            for row in csv.reader(issues_file):
                issues.append({
                    'title': row[0],
                    # Github requires carridge returns it seems
                    'body': row[1].replace("\\n", "\n")
                })

        return issues
