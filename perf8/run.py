from perf8.watcher import WatchedProcess, generate_plot


def main():
    report = "report.csv"
    p = WatchedProcess(sys.argv[1:], report)
    asyncio.run(p.run())
    generate_plot(report)


if __name__ == "__main__":
    main()
