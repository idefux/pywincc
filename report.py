from jinja2 import Environment, FileSystemLoader
from helper import str_to_datetime, datetime_to_str_without_ms, datetime_to_str_underscores,\
    date_to_str, datetime_is_date, date_to_str_underscores
import logging

def generate_alarms_report(alarms, begin_time, end_time, host_description='', filter_text=''):

    env = Environment(loader=FileSystemLoader('./reports/templates/'))
    template = env.get_template("alarms.html")
    
    dt_begin_time = str_to_datetime(begin_time)
    dt_end_time = str_to_datetime(end_time)
    
    if datetime_is_date(dt_begin_time) and datetime_is_date(dt_end_time):
        date_str = date_to_str(dt_begin_time.date())
        date_str_file = date_to_str_underscores(dt_begin_time.date())
    else:        
        date_str = "{0} - {1}".format(datetime_to_str_without_ms(dt_begin_time), datetime_to_str_without_ms(dt_end_time))
        date_str_file = "{0}_{1}".format(datetime_to_str_underscores(dt_begin_time), datetime_to_str_underscores(dt_end_time))
        
    if filter_text != '':
        filter_text_out = u"This is NOT a full list of alarms in the given time."
        filter_text_out += u"\n<br>\n"
        filter_text_out += u"Following filter was applied to search: TEXT LIKE '%{0}%'".format(filter_text)
    else:
        filter_text_out = filter_text                
    
    template_vars = {"title" : "Alarms Report", "alarms" : alarms, "state_dict" : alarms.state_dict,
                     "plant" : host_description, "count": alarms.get_count_grouped(),
                     "date_str" : date_str, "filter_text" : filter_text_out}
    
    html_out = template.render(template_vars)

    filename = "./reports/_out/alarms_{0}_{1}.html".format(host_description.replace(' ', '_'), date_str_file)
    logging.debug("Opering file {0} for printing the report.".format(filename))   
    with open(filename, "wb") as fh:
        fh.write(html_out.encode('utf-8'))
    
def operator_messages_report(operator_messages, begin_time, end_time, host_description=''):
    
    env = Environment(loader=FileSystemLoader('./reports/templates/'))
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
