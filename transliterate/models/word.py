# cd /odoo/./use_odoo
# pip install transliterate

from odoo import api, fields, models
from transliterate import translit
from transliterate.discover import autodiscover
from transliterate.base import TranslitLanguagePack, registry
from transliterate import detect_language


class Words(models.Model):

    _inherit = 'open.word'
    # _order = "name, frequency_store"

    transliteration = fields.Char(string='Transliteration', compute='_transliterate', store=True)

    frequency = fields.Integer(string='Frequency', default=-1)
    point_ids = fields.One2many('open.point', 'word_id')
    # frequency_store = fields.Integer(related='frequency', string='Frequency', store=True)
    #
    # @api.one
    # @api.onchange('point_ids')
    # def _compute_frequency(self):
    #     self.frequency = len(self.point_ids)

    @api.one
    def _transliterate(self):
        registry.register(HebrewLanguagePack, force=True)
        registry.register(GreekLanguagePack, force=True)
        if self.lang_id.code == 'el_GR':
            self.transliteration = translit(self.name, 'el', reversed=True)
        else:
            self.transliteration = translit(self.name, 'he', reversed=True)

    # @api.model
    # def _generate_order_by(self, order_spec, query):
    #     """
    #     Attempt to construct an appropriate ORDER BY clause based on order_spec, which must be
    #     a comma-separated list of valid field names, optionally followed by an ASC or DESC direction.
    #
    #     :raise ValueError in case order_spec is malformed
    #     """
    #     order_by_clause = ''
    #     order_spec = order_spec or self._order
    #     if order_spec:
    #         order_by_elements = self._generate_order_by_inner(self._table, order_spec, query)
    #         if order_by_elements:
    #             order_by_clause = ",".join(order_by_elements)
    #
    #     return order_by_clause and (' ORDER BY %s ' % order_by_clause) or ''


class GreekLanguagePack(TranslitLanguagePack):
    language_code = "el"
    language_name = "Greek"
    mapping = (
        u"abgdezhiklmnxoprstyfwuABGDEZHIKLMNXOPRSTYFWU",
        u"αβγδεζηικλμνξοπρστυφωθΑΒΓΔΕΖΗΙΚΛΜΝΞΟΠΡΣΤΥΦΩΘ",
    )
    reversed_specific_pre_processor_mapping = {
        u"Ά": u"A", u"ά": u"a",    # Ά, ά
        u"Α": u"A", u"α": u"a",    # Α, α
        u"Β": u"B", u"β": u"b",    # Β, β
        u"Γ": u"G", u"γ": u"g",    # Γ, γ
        u"Δ": u"D", u"δ": u"d",    # Δ, δ
        u"Ε": u"E", u"ε": u"e",    # Ε, ε
        u"Ζ": u"Z", u"ζ": u"z",    # Ζ, ζ
        u"Η": u"I", u"η": u"i",    # Η, η
        u"Θ": u"Th", u"θ": u"th",  # Θ, θ
        u"Ι": u"I", u"ι": u"i",    # Ι, ι
        u"Κ": u"K", u"κ": u"k",    # Κ, κ
        u"Λ": u"L", u"λ": u"l",    # Λ, λ
        u"Μ": u"M", u"μ": u"m",    # Μ, μ
        u"Ν": u"N", u"ν": u"n",    # Ν, ν
        u"Ξ": u"X", u"ξ": u"x",    # Ξ, ξ
        u"Ο": u"O", u"ο": u"o",    # Ο, ο
        u"Π": u"P", u"π": u"p",    # Π, π
        u"Ρ": u"R", u"ρ": u"r",    # Ρ, ρ
        u"Σ": u"S", u"σ": u"s",    # Σ, σ
        u"ἆ": u"a",                    # ς
        u"ἃ": u"a",                    # ς
        u"ἂ": u"a",                    # ς
        u"ᾳ": u"a",                    # ς
        u"ἤ": u"e",                    # ς
        u"ᾖ": u"e",                    # ς
        u"ἠ": u"e",                    # ς
        u"ς": u"s",                    # ς
        u"ὖ": u"u",                    # ς
        u"ὓ": u"u",                    # ς
        u"ὔ": u"u",                    # ς
        u"ὤ": u"o",                    # ς
        u"ὥ": u"o",                    # ς
        u"ὦ": u"o",                    # ς
        u"ὠ": u"o",                    # ς
        u"ὼ": u"o",                    # ς
        u"Ὦ": u"O",                    # ς
        u"ἷ": u"i",                    # ς
        u"Τ": u"T", u"τ": u"t",    # Τ, τ
        u"Υ": u"Y", u"υ": u"u",    # Υ, υ
        u"Χ": u"Ch", u"χ": u"ch",  # Χ, χ
        u"Ψ": u"Ps", u"ψ": u"ps",  # Ψ, ψ
        u"Ω": u"O", u"ω": u"o",    # Ω, ω
        u"Έ": u"E", u"έ": u"e",    # Έ, έ
        u"Ή": u"I", u"ή": u"i",    # Ή, ή
        u"Ί": u"I", u"ί": u"i",    # Ί, ί
        u"Ό": u"O", u"ό": u"o",    # Ό, ό
        u"Ύ": u"Y", u"ύ": u"u",    # Ύ, ύ
        u"Ώ": u"O", u"ώ": u"o",    # Ώ, ώ
        u"Ϊ": u"I", u"ϊ": u"i",    # Ϊ, ϊ
        u"Ϋ": u"Y", u"ϋ": u"u",    # Ϋ, ϋ
        u"ώ": u"o", u"ῦ": u"u",  # Ϋ, ϋ
        u"ῶ": u"o", u"ὐ": u"u",  # Ϋ, ϋ
        u"ᾧ": u"o", u"ὰ": u"a",  # Ϋ, ϋ
        u"ἡ": u"e", u"ή": u"e",  # Ϋ, ϋ
        u"ά": u"a", u"ἐ": u"e",  # Ϋ, ϋ
        u"ᾷ": u"a", u"ῇ": u"e",  # Ϋ, ϋ
        u"ὅ": u"o", u"ῷ": u"o",  # Ϋ, ϋ
        u"ό": u"o", u"ὲ": u"e",  # Ϋ, ϋ
        u"ὴ": u"e", u"ὁ": u"o",  # Ϋ, ϋ
        u"ῖ": u"i", u"ί": u"i",  # Ϋ, ϋ
        u"ᾶ": u"a", u"έ": u"e",  # Ϋ, ϋ
        u"ἀ": u"a", u"ὸ": u"o",  # Ϋ, ϋ
        u"ὑ": u"u", u"ῆ": u"e",  # Ϋ, ϋ
        u"ἔ": u"e", u"ἦ": u"e",  # Ϋ, ϋ
        u"ὀ": u"o", u"ύ": u"u",  # Ϋ, ϋ
        u"ῳ": u"o", u"ὕ": u"u",  # Ϋ, ϋ
        u"ὡ": u"o", u"ἄ": u"a",  # Ϋ, ϋ
        u"ῥ": u"r", u"ὃ": u"o",  # Ϋ, ϋ
        u"ὶ": u"i", u"ἵ": u"i",  # Ϋ, ϋ
        u"ἶ": u"i", u"ἢ": u"e",  # Ϋ, ϋ
        u"ἥ": u"e", u"ὺ": u"u",  # Ϋ, ϋ
        u"ἕ": u"e", u"ἁ": u"a",  # Ϋ, ϋ
        u"ΰ": u"u", u"ἑ": u"e",  # Ϋ, ϋ
        u"ὗ": u"u", u"ἴ": u"i",  # Ϋ, ϋ
        u"ῃ": u"e", u"ὧ": u"o",  # Ϋ, ϋ
        u"ἧ": u"e", u"ὄ": u"o",  # Ϋ, ϋ
    }


class HebrewLanguagePack(TranslitLanguagePack):
    language_code = "he"
    language_name = "Hebrew"
    mapping = (
        u"a",
        u"א",
    )
    reversed_specific_pre_processor_mapping = {
        u"\u0027": u"",  # '

        # Consonants
        u"\u05D0": u"",  # א
        u"\u05D1": u"V",  # ב
        u"\u05D1" + u"\u05BC": u"B",  # בּ
        u"\uFB31": u"B",  # בּ
        u"\u05D2": u"G",  # ג
        u"\u05D2" + u"\u05BC": u"G",  # גּ
        u"\uFB32": u"G",  # גּ‬‬
        u"\u05D2" + u"\u05F3": u"J",  # ג׳
        u"\u05D3": u"D",  # ד
        u"\u05D3" + u"\u05BC": u"D",  # דּ
        u"\uFB33": u"D",  # דּ
        u"\u05D3" + u"\u05F3": u"DH",  # ד׳
        u"\u05D4": u"H",  # ה
        u"\u05D4" + u"\u05BC": u"H",  # הּ
        u"\uFB34": u"H",  # הּ
        u"\u05D5": u"V",  # ו‬
        u"\u05D5" + u"\u202C": u"V",  # ו‬
        u"\u05D5" + u"\u05BC": u"V",  # וּ
        # u"\uFB35":             u"V",  # וּ  # To vowels u"U"
        u"\u05D6": u"Z",  # ז
        u"\u05D6" + u"\u05BC": u"Z",  # זּ
        u"\uFB36": u"Z",  # זּ‬
        u"\u05D6" + u"\u05F3": u"ZH",  # ז׳
        u"\u05D7": u"CH",  # ח
        u"\u05D8": u"T",  # ט
        u"\u05D8" + u"\u05BC": u"T",  # טּ
        u"\uFB38": u"T",  # טּ
        u"\u05D9": u"Y",  # י
        u"\u05D9" + u"\u05BC": u"Y",  # יּ
        u"\u05D9" + u"\u05BC" +
        u"\u202C": u"Y",  # יּ‬
        u"\uFB39": u"Y",  # יּ‬
        u"\u05DB": u"CH",  # כ
        u"\u05DB" + u"\u05BC": u"CH",  # כּ
        u"\u05DB" + u"\u05BC" +
        u"\u202C": u"CH",  # כּ
        u"\uFB3B": u"C",  # כּ
        u"\u05DA": u"CH",  # ך
        u"\u05DA" + u"\u05BC": u"CH",  # ךּ
        u"\u05DA" + u"\u05BC" +
        u"\u202C": u"CH",  # ךּ‬
        u"\uFB3A": u"CH",  # ךּ
        u"\u05DC": u"L",  # ל‬
        u"\u05DC" + u"\u05BC": u"L",  # לּ
        u"\uFB3C": u"L",  # לּ
        u"\u05DD": u"M",  # ם
        u"\u05DE": u"M",  # מ‬
        u"\u05DE" + u"\u05BC": u"M",  # מּ
        u"\uFB3E": u"M",  # מּ‬
        u"\u05DF": u"N",  # ן
        u"\u05E0": u"N",  # נ
        u"\u05E0" + u"\u05BC": u"N",  # נּ
        u"\uFB40": u"N",  # נּ
        u"\u05E1": u"S",  # ס
        u"\u05E1" + u"\u05BC": u"S",  # סּ
        u"\uFB41": u"S",  # סּ
        u"\u05E2": u"",  # ע
        u"\u05E3": u"F",  # ף
        u"\u05E3" + u"\u05BC": u"P",  # Possible problem u05BC # ףּ
        u"\uFB43": u"P",  # ףּ
        u"\u05E4": u"F",  # פ‬
        u"\u05E4" + u"\u05BC": u"P",  # פּ
        u"\uFB44": u"P",  # פּ
        u"\u05E5": u"TZ",  # ץ
        u"\u05E5" + u"\u05F3": u"TSH",  # Possible problem u05F3  # ץ׳
        u"\u05E6": u"TZ",  # צ‬
        u"\u05E6" + u"\u05BC": u"TZ",  # צּ
        u"\uFB46": u"TZ",  # צּ‬
        u"\u05E6" + u"\u05F3": u"TSH",  # Possible problem u05F3  # צ׳
        u"\u05E7": u"Q",  # ק
        u"\u05E7" + u"\u05BC": u"Q",  # קּ
        u"\uFB47": u"Q",  # קּ‬
        u"\u05E8": u"R",  # ר
        u"\u05E8" + u"\u05BC": u"R",  # רּ
        u"\uFB48": u"R",  # רּ
        u"\u05E9": u"S",  # ש
        u"\u05E9" + u"\u05BC": u"S",  # שּ
        u"\uFB49": u"S",  # שּ‬
        u"\u05E9" + u"\u05C2" +
        u"\u202C": u"S",  # שׂ
        u"\uFB2B": u"S",  # שׂ
        u"\u05E9" + u"\u05C1": u"SH",  # שׁ
        u"\uFB2A": u"SH",  # שׁ
        u"\u05E9" + u"\u05BC" +
        u"\u05C2" + u"\u202C": u"S",  # שּׂ‬
        u"\uFB2D": u"S",  # שּׂ
        u"\u05EA": u"T",  # ת
        u"\u05EA" + u"\u05BC": u"T",  # תּ
        u"\uFB4A": u"T",  # תּ
        u"\u05EA" + u"\u05F3": u"T",  # ת׳

        # Niqqud vowels
        u"\u05B0": u"e",  # ( ְ‬ )
        u"\u05B1": u"e",  # ( ֱ )
        u"\u05B2": u"a",  # ( ֲ )
        u"\u05B3": u"o",  # ( ֲ )
        u"\u05B4": u"i",  # ( ִ )
        u"\u05B5": u"e",  # ( ֵ )
        u"\u05B6": u"e",  # ( ֶ )
        u"\u05B7": u"a",  # ( ַ )
        u"\u05B8": u"a",  # ( ָ ) # It could be u"A" too
        u"\u05B9": u"o",  # ( ֹ )
        u"\u05BB": u"u",  # ( ֻ )
        u"\u05D5" + u"\u05BC": u"u",  # ( וּ )
        u"\uFB35": u"u",  # ( וּ )

        u"\u05C3": u":",
        u"\u05C0": u"|",
        u"\u05be": u"-",
        u"\u05f3": u"'",
        u"\u05f4": u"\u0022",
        u"\u05C6": u";",

        u"\u05BD": u",",
        u"\u05BF": u"'",
        u"\u05C1": u"",
        u"\u05C2": u"h",
        u"\u05C4": u"'",
        u"\u05C5": u".",

        u"\u05F0": u"W",
        # u"\u05F1": u"vy",
        # u"\u05F2": u"yy",

        # Diphthongs
        u"\u05B5" + u"\u05D9": u"ei",  # ( ֵי )
        u"\u05B6" + u"\u05D9": u"ei",  # ( ֶי )
        u"\u05B7" + u"\u05D9": u"ai",  # ( ַי )
        u"\u05B7" + u"\u05D9" +
        u"\u05B0": u"ai",  # ( ַיְ )
        u"\u05B7" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ai",  # ( ַיְ‬ )
        u"\u05B8" + u"\u05D9": u"ai",  # ( ָי )
        u"\u05B8" + u"\u05D9" +
        u"\u202C": u"ai",  # ( ָי‬ )
        u"\u05B8" + u"\u05D9" +
        u"\u05B0": u"ai",  # ( ָיְ )
        u"\u05B8" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ai",  # ( ָיְ‬ )
        u"\u05B9" + u"\u05D9": u"oi",  # ( ֹי )
        u"\u05B9" + u"\u05D9" +
        u"\u05B0": u"oi",  # ( ֹיְ )
        u"\u05B9" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"oi",  # ( ֹיְ‬ )
        u"\u05BB" + u"\u05D9": u"ui",  # ( ֻי )
        u"\u05BB" + u"\u05D9" +
        u"\u05B0": u"ui",  # ( ֻיְ )
        u"\u05BB" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ui",  # ( ֻיְ‬ )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9": u"ui",  # ( וּי )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9" + u"\u05B0": u"ui",  # ( וּיְ )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9" + u"\u05B0" +
        u"\u202C": u"ui",  # ( וּיְ‬ )
    }

