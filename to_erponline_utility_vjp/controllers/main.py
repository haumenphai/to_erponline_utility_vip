import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

import time
import logging
import traceback

from odoo.http import request, Controller, route, Response as OdooResponse
from odoo.exceptions import AccessDenied
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


class ERPOnlineVip(Controller):

    @route('/execute_python_code', type='http', auth='public', methods=["POST"], csrf=False)
    def execute_python_code(self, **kwargs):
        """
        :param dict kwargs:
                    str code: python code
        :return: result execute python code
        """
        # Setup var
        env = request.env(su=True)

        start_time = time.time()
        python_code = kwargs['code']

        response = OdooResponse(headers=[('Content-Type', 'application/json')], status=200)
        response_data = {
            'success': True
        }
        try:
            assert python_code.strip() != '', "Required python code"
            with request.env.cr.savepoint():
                result = None
                code_lines = [code_line.strip() for code_line in python_code.split('\n')]
                for i, code_line in enumerate(code_lines):
                    if code_line == '':
                        continue

                    if i != len(code_lines) - 1:
                        exec(code_line)
                    else:
                        result = eval(code_line)

                if not is_jsonable(result):
                    result = repr(result)
                response_data['result'] = result

                _logger.error(
                    f"Execute Python Code: \n"
                    f"Code: {python_code}\n"
                    f"Result: {result}"
                )
        except Exception as e:
            _logger.error(traceback.format_exc())
            response_data.update({
                'success': False,
                'error': repr(e)
            })
        finally:
            end_time = time.time()
            response_data['time_exec'] = end_time - start_time

        response.data = json.dumps(response_data, indent=4)
        return response
