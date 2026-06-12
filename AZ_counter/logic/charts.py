import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def avg_score_schedule(history):
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(range(len(history)), history)
    ax.set_title("График среднего балла")
    ax.set_ylim(1, 6)
    return fig