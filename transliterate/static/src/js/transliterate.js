odoo.define('transliterate.transliterate', function (require) {
'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var _t = core._t;

    if ($('.o_compute_frequency').length) {
        var compute_frequency = function () {
            var word = $("input[name='word']").val();
            ajax.jsonRpc('/compute/f/', 'call', {
                word_id: word,
                }).then(function (data) {
                    if (data.word_id != null){
                        $("h5[name='word']").empty().text(data.name + ' > ' + data.frequency);
                        $("input[name='word']").val(data.word_id);
                        compute_frequency();
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_compute_frequency').ready(function(){
            compute_frequency();
        });
    }

//    ADD NEW LANGUAGE

    if ($('.o_dictionary').length) {
        $('.o_dictionary').ready(function(){
            $("div[id='translate_this']").append(
                '<a href="/new/language/" class="btn btn-sm btn-primary">Add new language</a>'
            ).show()
        });
    }

});