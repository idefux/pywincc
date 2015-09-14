function alarm_filter() {
    if (document.getElementById('check_come').checked == 1) {
        $(".alCOME").removeClass("hidden-row");
    } else {
        $(".alCOME").addClass("hidden-row");
    }
    if (document.getElementById('check_go').checked == 1) {
        $(".alGO").removeClass("hidden-row");
    } else {
        $(".alGO").addClass("hidden-row");
    }
    if (document.getElementById('check_ack_gack').checked == 1) {
        $(".alACK").removeClass("hidden-row");
        $(".alGACK").removeClass("hidden-row");
    } else {
        $(".alACK").addClass("hidden-row");
        $(".alGACK").addClass("hidden-row");
    }
    if (document.getElementById('check_warning').checked == 1) {
        $(".alWARNING").removeClass("hidden-row");
    } else {
        $(".alWARNING").addClass("hidden-row");
    }
    if (document.getElementById('check_error_day').checked == 1) {
        $(".alERROR_DAY").removeClass("hidden-row");
    } else {
        $(".alERROR_DAY").addClass("hidden-row");
    }
    if (document.getElementById('check_error_now').checked == 1) {
        $(".alERROR_NOW").removeClass("hidden-row");
    } else {
        $(".alERROR_NOW").addClass("hidden-row");
    }
    if (document.getElementById('check_stop_all').checked == 1) {
        $(".alSTOP_ALL").removeClass("hidden-row");
    } else {
        $(".alSTOP_ALL").addClass("hidden-row");
    }
}
