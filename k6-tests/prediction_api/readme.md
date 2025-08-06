# Generating a diff Flamegraph for prediction APIs
## Flamegraph definition
A flamegraph is a visualization of profiled software performance data that shows how much CPU time is spent in each function call. It represents the call stack as stacked bars where wider bars indicate more time spent, making it easy to identify performance bottlenecks.
## Diff Flamegraph
A diff flamegraph compares two flamegraphs—such as before and after a code change or between two implementations—to highlight differences in CPU usage. It helps quickly spot which functions consume more or less CPU time between the two runs.
## Workflow of the Diff Flamegraph
In this use case we have created two kinds of prediction APIs with the same goal: Display EHT/EUR price predictions. One API was written in rust axum included in the folder `services/prediction-api` and the other one was written in python FastAPI included in `services/prediction_api_py`.

The idea is to generate a diff flamegraph between both APIs considering the one written in python is the baseline one because most of the project is coded in such language.

### Prerequisites
You should first install the `perf` which is a powerful Linux performance analysis tool that collects CPU profiling data and other hardware/software event metrics regardless of the programming language used. It helps developers understand where their programs spend time by sampling stack traces, enabling the creation of flamegraphs and detailed performance reports.

You can find the installation instructions of `perf` iw wsl2 right [here](https://www.arong-xu.com/en/posts/wsl2-install-perf-with-manual-compile/).
