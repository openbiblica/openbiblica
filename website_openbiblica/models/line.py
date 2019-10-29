from odoo import api, fields, models
import re


class Lines(models.Model):
    _inherit = 'open.line'

    # @api.one
    def _interlinear_line(self):
        if self.lang_id.direction == 'rtl':
            words = self.name.split()
        else:
            words = re.findall(r'\w+|[\[\]⸂⸃()]|\S+', self.name)
        sequence = 1
        for word in words:
            word_id = self.env['open.word'].search([('name', '=', word), ('lang_id', '=', self.lang_id.id)])
            if not word_id:
                word_id = self.env['open.word'].create({
                    'name': word,
                    'lang_id': self.lang_id.id,
                    'forum_id': self.forum_id.id,
                    'create_id': self.create_id.id,
                })
            # if word_id.frequency < 1:
            #     word_id.frequency = 1
            # else:
            #     word_id['frequency'] += 1
            self.env['open.point'].create({
                'line_id': self.id,
                'word_id': word_id.id,
                'create_id': self.create_id.id,
                'sequence': sequence,
            })
            sequence += 1
        self['is_interlinear'] = True
        return

