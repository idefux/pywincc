from jinja2 import Environment, FileSystemLoader
from helper import str_to_datetime, datetime_to_str_without_ms, datetime_to_str_underscores

def alarms_report(alarms, begin_time, end_time, host_description=''):

    env = Environment(loader=FileSystemLoader('./reports/'))
    template = env.get_template("alarms.html")
    
    dt_begin_time = str_to_datetime(begin_time)
    dt_end_time = str_to_datetime(end_time)
    
    template_vars = {"title" : "Alarms Report", "alarms_log" : alarms.to_html(),
                     "plant" : host_description, "alarms_grouped_priority" : alarms.count_grouped_to_html(),
                     "begin_time" : datetime_to_str_without_ms(dt_begin_time), "end_time" : datetime_to_str_without_ms(dt_end_time)}
    
    html_out = template.render(template_vars)
    #print html_out

    with open("./reports/_out/alarms_{0}_{1}.html".format(datetime_to_str_underscores(dt_begin_time), datetime_to_str_underscores(dt_end_time)), "wb") as fh:
        fh.write(html_out.encode('utf-8'))
    
def operator_messages_report(operator_messages, begin_time, end_time, host_description=''):
    
    env = Environment(loader=FileSystemLoader('./reports/'))
    template = env.get_template("operator_messages.html")
    
    dt_begin_time = str_to_datetime(begin_time)
    dt_end_time = str_to_datetime(end_time)
    
    template_vars = {"title" : "Operator Messages Report", "operator_messages_log" : operator_messages.to_html(),
                     "plant" : host_description, "operator_messages_count" : operator_messages.count(),
                     "begin_time" : datetime_to_str_without_ms(dt_begin_time), "end_time" : datetime_to_str_without_ms(dt_end_time)}
    
    html_out = template.render(template_vars)
    #print html_out

    with open("./reports/_out/operator_messages_{0}_{1}.html".format(datetime_to_str_underscores(dt_begin_time), datetime_to_str_underscores(dt_end_time)), "wb") as fh:
        fh.write(html_out.encode('utf-8'))
