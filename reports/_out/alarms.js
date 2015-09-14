function alarm_filter() {
    // Make all rows visible
    $(".alCOME").removeClass("hidden-row");
    $(".alGO").removeClass("hidden-row");
    $(".alACK").removeClass("hidden-row");
    $(".alGACK").removeClass("hidden-row");
    // Hide rows based on settings
    if (document.getElementById('check_come').checked == 0) {
        $(".alCOME").addClass("hidden-row");
    }
    if (document.getElementById('check_go').checked == 0) {
        $(".alGO").addClass("hidden-row");
    }
    if (document.getElementById('check_ack_gack').checked == 0) {
        $(".alACK").addClass("hidden-row");
        $(".alGACK").addClass("hidden-row");
    }
    if (document.getElementById('check_warning').checked == 0) {
        $(".alWARNING").addClass("hidden-row");
    }
    if (document.getElementById('check_error_day').checked == 0) {
        $(".alERROR_DAY").addClass("hidden-row");
    }
    if (document.getElementById('check_error_now').checked == 0) {
        $(".alERROR_NOW").addClass("hidden-row");
    }
    if (document.getElementById('check_stop_all').checked == 0) {
        $(".alSTOP_ALL").addClass("hidden-row");
    }
}
