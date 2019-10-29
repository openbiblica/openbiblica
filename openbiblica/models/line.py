from odoo import api, fields, models, tools


class Lines(models.Model):

    _name = "open.line"
    _description = "Lines"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "content_seq, part_seq, sequence"

    lang_id = fields.Many2one(related='part_id.lang_id')
    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')
    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)
    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='part_id.forum_id')
    post_ids = fields.One2many('forum.post', 'line_id', string='Comments')
    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_id = fields.Many2one('open.line', 'Main Source')
    source_ids = fields.Many2many('open.line', 'line_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    is_interlinear = fields.Boolean('Interlinear')
    is_transcription = fields.Boolean('Transcription')
    # manuscript_ids = fields.Many2many('slide.slide', string='Manuscript Sources')
    # manuscript_id = fields.Many2one('slide.slide', string='Main Manuscript Source')

    name = fields.Text('Plain Content', compute='_get_plain_content', store=True)
    content = fields.Html('Content', strip_style=True)

    sequence = fields.Integer('Sequence', required=True)
    part_seq = fields.Integer('Part Sequence', compute='_compute_part_sequence')
    content_seq = fields.Integer('Content Sequence', compute='_compute_content_sequence')
    chapter = fields.Char('Chapter')
    chapter_alt = fields.Char('Alternative Chapter')
    verse = fields.Char('Verse')
    verse_alt = fields.Char('Alternative Verse')
    verse_char = fields.Char('Verse Character')
    page = fields.Integer('Page Number')

    is_title = fields.Boolean('This is a title')
    style = fields.Char('Style')
    align = fields.Char('Align')
    insert_paragraph = fields.Boolean('Insert paragraph tab')
    insert_breakline = fields.Boolean('Insert break line before text')
    insert_pagebreak = fields.Boolean('Insert page break before text')

    biblica_id = fields.Many2one(related='part_id.biblica_id')
    content_id = fields.Many2one(related='part_id.content_id')
    subcontent_id = fields.Many2one(related='part_id.subcontent_id')
    part_id = fields.Many2one('open.part', string='Part')
    point_ids = fields.One2many('open.point', 'line_id', string='Points')

    @api.one
    @api.depends('content')
    def _get_plain_content(self):
        self.name = tools.html2plaintext(self.content)[0:500] if self.content else False

    @api.depends('part_id.sequence')
    def _compute_part_sequence(self):
        for line in self:
            if line.part_id:
                line.part_seq = line.part_id.sequence

    @api.depends('content_id.sequence')
    def _compute_content_sequence(self):
        for line in self:
            if line.content_id:
                line.content_seq = line.content_id.sequence
