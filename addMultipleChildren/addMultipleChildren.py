# addMultipleChildren plugin

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.api import ITemplateStreamFilter
from trac.web.main import IRequestHandler
from trac.util import get_reporter_id
import re
from trac.ticket import model
from ast import literal_eval
from genshi.builder import tag
from genshi.filters import Transformer

class SubTicketsStringError(Exception):
    def __init__(self, message):
        self.message = message

def parseSubTicketString(string):
    """Receives a formatted string and returns a list of ticket objects.
    
    The input string should be of the form:
    - estimate This is the summary
    This is the description.
    Each ticket object has the following fields:
      - summary
      - description
      - estimate

    Every new ticket should start with a '-' at the beginning of the line.
    Then the estimate should follow (a float or integer).
    Then a space and the rest of the line is the summary.
    Below that line the whole text, until the next '-' contains the description."""
    string = string.strip()
    if not string:
        return []
    if string[0] != '-':
        raise SubTicketsStringError(
            """The sub ticket string should start with a '-'.""")
    string = string[1:]
    def _parseSubTicket(sub_ticket):
        split = sub_ticket.split('\n', 1)
        first_line = split[0].split(' ', 2)
        first_line_error = """The first line of a sub ticket string should be of the form:
'-<space><estimate><space><summary>' where the '<estimate>' is optional or should be float or an int.
In case the estimate is omitted, the line SHOULD have 2 spaces after the '-'."""
        if len(first_line) != 3:
            raise SubTicketsStringError(first_line_error)
        if first_line[0] != '':
            raise SubTicketsStringError(first_line_error)
        summary = first_line[2]
        try:
            if first_line[1]:
                float(first_line[1])
        except ValueError:
            raise SubTicketsStringError(first_line_error)
        estimate = first_line[1]

        if len(split) > 1:
            description = split[1]
        else:
            description = ""
        class Ticket:
            pass
        t = Ticket()
        t.summary = summary
        t.description = description
        t.estimate = estimate
        return t
    return map(_parseSubTicket, string.split('\n-'))
    

class AddMultipleChildrenPlugin(Component):
    """A plugin to create a number of child tickets at once.
    It relies on the custom fields 'cl_product' and 'estimate' being present.
    """
    implements(IRequestHandler, 
               ITemplateProvider, 
               ITemplateStreamFilter)

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/addmultiplechildren/([0-9]+)$', req.path_info)
        if match:
            req.args['ticket'] = match.group(1)
            return True

    def process_request(self, req):
        ticket = model.Ticket(self.env, req.args.get('ticket'))
        data = {'ticket': ticket,
                'version': None,
                'split_string_error': None,
                'split_string_error_line_count': 0,
                'show_split_string_error': False,
                'split_string': ""}
        add_stylesheet(req, 'common/css/ticket.css')
        add_stylesheet(req, 'hw/css/addMultipleChildren.css')
        if req.method == 'POST':
            def _create_sub_tickets(self, string):
                sub_tickets = parseSubTicketString(string)
                for s in sub_tickets:
                    t = model.Ticket(self.env)
                    t['status'] = 'new'
                    t['summary'] = s.summary
                    t['description'] = s.description
                    t['parents'] = str(ticket.id)
                    t['reporter'] = get_reporter_id(req)
                    t['estimate'] = s.estimate
                    t['cl_product'] = ticket['cl_product']
                    t['type'] = 'task'
                    t.insert()
            split_string = req.args['addMultipleChildren']
            try:
                _create_sub_tickets(self, split_string)
                req.redirect(req.href.ticket(ticket.id))
            except SubTicketsStringError as error:
                data['split_string_error'] = error.message
                data['split_string_error_line_count'] = error.message.count('\n') + 2
                data['show_split_string_error'] = True
                data['split_string'] = split_string
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'addMultipleChildren.html', data, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
 
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith('/ticket/'):
            ticket = data.get('ticket')
            div = tag.div(tag.a("Create Multiple Children", href=(req.href.addmultiplechildren() + "/%s" % ticket.id)))
            stream |= Transformer('.//div[@id="ticket"]').append(div)

        return stream
