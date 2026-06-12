class Calculator:
    def __init__(self, marks):
        self.marks = marks

    def avg_score(self, subject: str, slice_len: int = None) -> float:
        marks_count = 0
        marks_sum = 0
        for mark in self.marks[subject][0][:slice_len]:
            marks_sum += int(mark[0])*int(mark[1])
            marks_count += int(mark[1])

        if marks_count > 0:
            return marks_sum/marks_count
        else:
            return 0.0

    def avg_score_history(self, subject):
        history = []
        for i in range(1, len(self.marks[subject][0])+1):
            history.append(self.avg_score(subject, i))
        return history