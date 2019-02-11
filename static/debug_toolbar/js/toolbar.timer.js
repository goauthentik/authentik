(function () {
    // Browser timing remains hidden unless we can successfully access the performance object
    var perf = window.performance || window.msPerformance ||
               window.webkitPerformance || window.mozPerformance;
    if (!perf)
        return;

    var rowCount = 0,
        timingOffset = perf.timing.navigationStart,
        timingEnd = perf.timing.loadEventEnd,
        totalTime = timingEnd - timingOffset;
    function getLeft(stat) {
        return ((perf.timing[stat] - timingOffset) / (totalTime)) * 100.0;
    }
    function getCSSWidth(stat, endStat) {
        var width = ((perf.timing[endStat] - perf.timing[stat]) / (totalTime)) * 100.0;
        // Calculate relative percent (same as sql panel logic)
        width = 100.0 * width / (100.0 - getLeft(stat));
        return (width < 1) ? "2px" : width + "%";
    }
    function addRow(stat, endStat) {
        rowCount++;
        var row = document.createElement('tr');
        row.className = (rowCount % 2) ? 'djDebugOdd' : 'djDebugEven';
        if (endStat) {
            // Render a start through end bar
            row.innerHTML = '<td>' + stat.replace('Start', '') + '</td>' +
                            '<td class="djdt-timeline"><div class="djDebugTimeline"><div class="djDebugLineChart"><strong>&#160;</strong></div></div></td>' +
                            '<td>' + (perf.timing[stat] - timingOffset) + ' (+' + (perf.timing[endStat] - perf.timing[stat]) + ')</td>';
            row.querySelector('strong').style.width = getCSSWidth(stat, endStat);
        } else {
            // Render a point in time
            row.innerHTML = '<td>' + stat + '</td>' +
                            '<td class="djdt-timeline"><div class="djDebugTimeline"><div class="djDebugLineChart"><strong>&#160;</strong></div></div></td>' +
                            '<td>' + (perf.timing[stat] - timingOffset) + '</td>';
            row.querySelector('strong').style.width = '2px';
        }
        row.querySelector('.djDebugLineChart').style.left = getLeft(stat) + '%';
        document.querySelector('#djDebugBrowserTimingTableBody').appendChild(row);
    }

    // This is a reasonably complete and ordered set of timing periods (2 params) and events (1 param)
    addRow('domainLookupStart', 'domainLookupEnd');
    addRow('connectStart', 'connectEnd');
    addRow('requestStart', 'responseEnd'); // There is no requestEnd
    addRow('responseStart', 'responseEnd');
    addRow('domLoading', 'domComplete'); // Spans the events below
    addRow('domInteractive');
    addRow('domContentLoadedEventStart', 'domContentLoadedEventEnd');
    addRow('loadEventStart', 'loadEventEnd');
    document.querySelector('#djDebugBrowserTiming').classList.remove('djdt-hidden');
})();
