# addMultipleChildren plugin

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import get_reporter_id
import re
from trac.ticket import model
from ast import literal_eval

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
            """The sub ticket string should start with a '-'.

%s""" % string)
    string = string[1:]
    def _parseSubTicket(sub_ticket):
        split = sub_ticket.split('\n', 1)
        first_line = split[0].strip().split(' ', 1)
        first_line_error = """The first line of a sub ticket string should be of the form:
'<estimate><space><summary>' where the '<estimate>' should be float or an int.

%s""" % split[0]
        if len(first_line) != 2:
            raise SubTicketsStringError(first_line_error)
        summary = first_line[1]
        try:
            float(first_line[0])
        except ValueError:
            raise SubTicketsStringError(first_line_error)
        estimate = first_line[0]

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
    return map(_parseSubTicket, string.split('-'))
    

class AddMultipleChildrenPlugin(Component):
    """A plugin to create a number of child tickets at once.
    It relies on the custom fields 'cl_product' and 'estimate' being present.
    """
    implements(IRequestHandler, ITemplateProvider)

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
                'split-string-error': None}
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
                    t.insert()
            split_string = req.args['addMultipleChildren']
            try:
                _create_sub_tickets(self, split_string)
                req.redirect(req.href.ticket(ticket.id))
            except SubTicketsStringError as error:
                data['split-string-error'] = error.message
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
 
