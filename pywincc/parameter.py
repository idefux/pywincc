"""Handle VAS S7 parameters"""

from collections import namedtuple

Parameter = namedtuple('Parameter',
                       'id textid helpid spsid pid tag text act min max default mul right sec grp unit helptext')


class ParameterRecord():

    def __init__(self):
        self.parameters = []

    def push(self, parameter):
        self.parameters.append(parameter)

    def __iter__(self):
        return iter(self.parameters)

    def __unicode__(self):
        output = u""
        len_t = self.max_length_text() + 1
        len_act = self.max_length_act() + 1
        len_min = self.max_length_min() + 1
        len_max = self.max_length_max() + 1
        len_def = self.max_length_def() + 1
        for p in self:
            output += u"{p.id:6} {p.spsid:1} {p.pid:4} {p.tag:24} ".format(p=p)
            output += u"{p.text:{len_t}} {p.act:{len_a}} ".format(p=p, len_t=len_t, len_a=len_act)
            output += u"{p.min:{len_min}} {p.max:{len_max}} {p.default:{len_def}} ".format(p=p, len_min=len_min, len_max=len_max, len_def=len_def)
            output += u"{p.sec:2} {p.grp:2} {p.right}\n".format(p=p)
        return output

    def __str__(self):
        return unicode(self).encode('utf-8')

    def to_csv(self, print_headers=True):
        csv = u""
        if print_headers:
            csv += u"ID;SPSID;PID;TAG;TEXT;ACTUAL VALUE;MIN VALUE;MAX VALUE;"
            csv += u"DEFAULT VALUE;MULTIPLICATOR;SECTION;GROUP;RIGHTS\n"
        for parameter in self:
            csv += u"{p.id:6};{p.spsid:1};{p.pid:4};{p.tag:24};{p.text};{p.act};".format(p=parameter)
            csv += u"{p.min};{p.max};{p.default};{p.mul};".format(p=parameter)
            csv += u"{p.sec};{p.grp};{p.right}\n".format(p=parameter)
        return csv
        
    def max_length_text(self):
        """Return the text length of longest parameter text."""
        p = max(self, key=lambda x: len(x.text))
        return len(p.text)

    # ===========================================================================
    # def max_length_x(self, key):
    #     """Return the text length of longest parameter text."""
    #     p = max(self, key=lambda x: len(str(eval("x." + key))))
    #     return len(p.text)
    # ===========================================================================

    def max_length_act(self):
        """Return the text length of longest act value."""
        p = max(self, key=lambda x: len(str(x.act)))
        return len(str(p.act))

    def max_length_min(self):
        """Return the text length of longest min value."""
        p = max(self, key=lambda x: len(str(x.min)))
        return len(str(p.min))

    def max_length_max(self):
        """Return the text length of longest max value."""
        p = max(self, key=lambda x: len(str(x.max)))
        return len(str(p.max))

    def max_length_def(self):
        """Return the text length of longest max value."""
        p = max(self, key=lambda x: len(str(x.default)))
        return len(str(p.default))
