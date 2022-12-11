# trick to replace the abs path in speedscope
# when it's ran used Docker
import os

HERE = os.path.abspath(os.path.dirname(__file__))

with open('perf8-report/pyspy.html') as f:
    data = f.read()

data = data.replace('/app/perf8-report/results.js', f'{HERE}/perf8-report/results.js')

with open('perf8-report/pyspy.html', 'w') as f:
    f.write(data)
