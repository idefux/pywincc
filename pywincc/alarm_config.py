"""Handle VAS S7 alarm configuration"""

from collections import namedtuple
from helper import datetime_to_str_slashes

AlarmConfig = namedtuple('Alarm',
                   'id textid helpid spsid aid tag text emsr0 emsr1 boin alarmout singleack alarmprior cfg grp coun alarmmaxcoun right helptext lastuser lastaccess updateenable changedbyplc changedbyhmi')

class AlarmConfigRecord():

    def __init__(self):
        self.alarmconfig = []

    def push(self, alarm):
        self.alarmconfig.append(alarm)

    def __iter__(self):
        return iter(self.alarmconfig)

    def __unicode__(self):
        output = u""
        len_t = self.max_length_text() + 1
        len_ht = self.max_length_helptext() + 1
        len_amc = self.max_length_alarmmaxcoun() + 1
        for a in self:
            output += u"{a.id:6} {a.spsid:1} {a.aid:4} {a.tag:24} ".format(a=a)
            output += u"{a.text:{len_t}} {a.emsr0:13} {a.emsr1:13}".format(a=a, len_t=len_t)
            output += u"{a.alarmprior:3} {a.cfg:3} {a.grp:3} {a.alarmmaxcoun:{len_amc}}".format(a=a, len_amc=len_amc)
            output += u"{a.right} {a.helptext:{len_ht}}\n".format(a=a, len_ht=len_ht)
        return output

    def __str__(self):
        return unicode(self).encode('utf-8')

    def to_csv(self, print_headers=True):
        csv = u""
        if print_headers:
            csv += u"ID;TEXTID;HELPID;SPSID;AID;Tag;ucText;ucEMSR0;ucEMSR1;boIn\
                     ;boAlarmOut;boSingleAck;ucAlarmPrior;ucCfg;ucGroup;ulCoun\
                     ;ulAlarmMaxCoun;ucRights;ucHelpText\
                     ;LastUser;LastAccess;UpdateEnable;ChangedByPLC;ChangedByHMI\n"
        for alarm in self:
            csv += u"{a.id};{a.textid};{a.helpid};{a.spsid};{a.aid};{a.tag};{a.text};".format(a=alarm)
            csv += u"{a.emsr0};{a.emsr1};{a.boin};{a.alarmout};{a.singleack};".format(a=alarm)
            csv += u"{a.alarmprior};{a.cfg};{a.grp};{a.coun};".format(a=alarm)
            csv += u"{a.alarmmaxcoun};{a.right};{a.helptext};".format(a=alarm)
            #csv += u"{a.lastuser};{lastaccess};{a.updateenable};{a.changedbyplc};{a.changedbyhmi}\n".format(a=alarm, lastaccess=datetime_to_str_slashes(alarm.lastaccess))
            csv += u"{a.lastuser};{a.lastaccess};{a.updateenable};{a.changedbyplc};{a.changedbyhmi}\n".format(a=alarm)
        return csv

    def max_length_text(self):
        """Return the text length of longest alarm text."""
        a = max(self, key=lambda x: len(x.text))
        return len(a.text)

    def max_length_helptext(self):
        """Return the text length of longest alarm helptext."""
        a = max(self, key=lambda x: len(x.helptext))
        return len(a.helptext)

    def max_length_alarmmaxcoun(self):
        """Return the text length of longest alarm max coun."""
        a = max(self, key=lambda x: len(str(x.alarmmaxcoun)))
        return len(str(a.alarmmaxcoun))
