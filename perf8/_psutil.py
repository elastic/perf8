import psutil
import csv
import matplotlib.pyplot as plt
import time


def generate_plot(path):
    x = []
    rss = []
    # cpu = []

    with open(path) as csvfile:
        lines = csv.reader(csvfile, delimiter=",")
        for i, row in enumerate(lines):
            if i == 0:
                continue
            x.append(row[-1])
            bytes = round(int(row[0]) / (1024 * 1024), 2)
            rss.append(bytes)  # rss
            # cpu.append(row[-1])

    # plt.plot(x, cpu, color="r", linestyle="dashed", marker="o", label="CPU %")
    plt.plot(x, rss, color="g", linestyle="dashed", marker="o", label="RSS")

    plt.xticks(rotation=25)
    plt.xlabel("Duration")
    plt.ylabel("Bytes")  # switch to KiB or MiB automatically - XXX
    plt.title("Performance Report", fontsize=20)
    plt.grid()
    plt.legend()
    plt.savefig("report.png")
    return "report.png"


class ResourceWatcher:
    name = "psutil"

    def __init__(self, **options):
        self.report_fd = self.writer = self.proc_info = None
        self.report_file = options.get("report_file", "report.csv")

    def start(self, pid):
        self.proc_info = psutil.Process(pid)
        self.report_fd = open(self.report_file, "w")
        self.writer = csv.writer(self.report_fd)
        self.started_at = time.time()
        self.rows = (
            "rss",
            "num_fds",
            "num_threads",
            "ctx_switch",
            "cpu_user",
            "cpu_system",
            "cpu_percent",
            "when",
            "since",
        )
        # headers
        self.writer.writerow(self.rows)

    async def probe(self, pid):
        info = self.proc_info.as_dict()
        probed_at = time.time()
        metrics = (
            info["memory_info"].rss,
            info["num_fds"],
            info["num_threads"],
            info["num_ctx_switches"].voluntary,
            info["cpu_times"].user,
            info["cpu_times"].system,
            info["cpu_percent"],
            probed_at,
            int(probed_at - self.started_at),
        )

        self.writer.writerow(metrics)
        self.report_fd.flush()

    def stop(self, pid):
        if self.report_fd is not None:
            self.report_fd.close()
            plot_file = generate_plot(self.report_file)
            return [plot_file, self.report_file]
        return []
