odoo.define('website_openbiblica.website_openbiblica', function (require) {
'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var _t = core._t;

    var lastsearch;

//    SEARCH MENU

    if ($('.o_bible_search').length) {
        var language_options = $("select[name='language_id']:enabled");
        var bible_options = $("select[name='bible_id']:enabled");
        var book_options = $("select[name='book_id']:enabled");
        var part_options = $("select[name='part_id']:enabled");
        var verse_options = $("select[name='verse_id']:enabled");

        $('.o_bible_search').ready(function(){
            bible_options.parent().hide();
            book_options.parent().hide();
            part_options.parent().hide();
            verse_options.parent().hide();
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (languages) {
                if (languages.length > 0){
                    var i;
                    for (i = 0; i < languages.length; i++) {
                        language_options.append('<option value="' + languages[i].id + '">' + languages[i].name + '</option>');
                    };
                };
            });
        });
        language_options.on('change', language_options, function () {
            bible_options.children('option:not(:first)').remove();
            book_options.children('option:not(:first)').remove();
            part_options.children('option:not(:first)').remove();
            verse_options.children('option:not(:first)').remove();
            bible_options.parent().hide();
            book_options.parent().hide();
            part_options.parent().hide();
            verse_options.parent().hide();
            var lang = language_options.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_options.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_options.parent().show();};
                };
            });
        });
        if (bible_options.length >= 1) {
            bible_options.on('change', bible_options, function () {
                book_options.children('option:not(:first)').remove();
                part_options.children('option:not(:first)').remove();
                verse_options.children('option:not(:first)').remove();
                book_options.parent().hide();
                part_options.parent().hide();
                verse_options.parent().hide();
                var bible = bible_options.val();
                ajax.jsonRpc('/get/book/', 'call', {
                      bible_id: bible,
                    }).then(function (book) {
                    if (book){
                        console.log(book);
                        var i;
                        for (i = 0; i < book.length; i++) {
                            book_options.append('<option value="' + book[i].id + '">' + book[i].name + '</option>');
                        };
                    if (i>0){book_options.parent().show();};
                    };
                });
            });
        }
        if (book_options.length >= 1) {
            book_options.on('change', book_options, function () {
                part_options.children('option:not(:first)').remove();
                verse_options.children('option:not(:first)').remove();
                part_options.parent().hide();
                verse_options.parent().hide();
                var book = book_options.val();
                ajax.jsonRpc('/get/part/', 'call', {
                      book_id: book,
                    }).then(function (part) {
                    if (part){
                        console.log(part);
                        var i;
                        for (i = 0; i < part.length; i++) {
                            part_options.append('<option value="' + part[i].id + '">' + part[i].name + '</option>');
                        };
                    if (i>0){part_options.parent().show();};
                    };
                });
            });
        }
        if (part_options.length >= 1) {
            part_options.on('change', part_options, function () {
                verse_options.children('option:not(:first)').remove();
                verse_options.parent().hide();
                var part = part_options.val();
                ajax.jsonRpc('/get/verse/', 'call', {
                      part_id: part,
                    }).then(function (verse) {
                    if (verse){
//                        console.log(verse);
                        var i;
                        for (i = 0; i < verse.length; i++) {
                            verse_options.append('<option value="' + verse[i].id + '">' + verse[i].name + '</option>');
                        };
                    if (i>0){verse_options.parent().show();};
                    };
                });
            });
        }
    }

//    USFM JSON

    if ($('.o_install_next').length) {
        $('.o_install_next').ready(function(){
            $("#install_next_button").click();
        });
    }

//    SELECT SOURCE

    if ($('.o_select_source').length) {
        $('.o_select_source').on('change', $("select[name='select_source']"), function () {
            $("#select_source_button").click();
        });
        $('.o_select_source').on('change', $("select[name='select_lang']"), function () {
            $("#select_source_button").click();
        });
    }

//    TRANSLATE THIS

    if ($('.o_translate_content').length) {
        $('.o_translate_content').ready(function(){
            var t_content_id = $("input[name='t_content_id']").val();
            var t_content_name = $("input[name='t_content_name']").val();
            $("div[id='translate_this']").append(
                '<a href="/translate/c/' + t_content_id + '" class="btn btn-sm btn-primary">Translate ' + t_content_name + '</a>'
            ).show()
        });
    }

//    ADD CONTENT SOURCE

    if ($('.o_add_content_source').length) {
        var language_source = $("select[name='language']:enabled");
        var bible_source = $("select[name='bible']:enabled");
        var book_source = $("select[name='s_content_id']:enabled");
        var submit = $("div[name='submit']");

        $('.o_add_content_source').ready(function(){
            bible_source.parent().hide();
            book_source.parent().hide();
            submit.hide()
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (languages) {
                if (languages.length > 0){
                    var i;
                    for (i = 0; i < languages.length; i++) {
                        language_source.append('<option value="' + languages[i].id + '">' + languages[i].name + '</option>');
                    };
                };
            });
        });
        language_source.on('change', language_source, function () {
            bible_source.children('option:not(:first)').remove();
            book_source.children('option:not(:first)').remove();
            bible_source.parent().hide();
            book_source.parent().hide();
            submit.hide()
            var lang = language_source.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_source.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_source.parent().show();};
                };
            });
        });
        if (bible_source.length >= 1) {
            bible_source.on('change', bible_source, function () {
                book_source.children('option:not(:first)').remove();
                book_source.parent().hide();
                submit.hide()
                var bible = bible_source.val();
                ajax.jsonRpc('/get/book/', 'call', {
                      bible_id: bible,
                    }).then(function (book) {
                    if (book){
                        console.log(book);
                        var i;
                        for (i = 0; i < book.length; i++) {
                            book_source.append('<option value="' + book[i].id + '">' + book[i].name + '</option>');
                        };
                    if (i>0){book_source.parent().show();};
                    };
                });
            });
        }
        if (book_source.length >= 1) {
            book_source.on('change', bible_source, function () {
                if ($(this).val() || 0){
                    submit.show();
                } else {
                    submit.hide();
                }
            });
        }
    }

//    ADD BIBLICA SOURCE

    if ($('.o_add_biblica_source').length) {
        var language_source = $("select[name='language']:enabled");
        var bible_source = $("select[name='bible']:enabled");
        var submit = $("div[name='submit']");

        $('.o_add_biblica_source').ready(function(){
            bible_source.parent().hide();
            submit.hide()
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (languages) {
                if (languages.length > 0){
                    var i;
                    for (i = 0; i < languages.length; i++) {
                        language_source.append('<option value="' + languages[i].id + '">' + languages[i].name + '</option>');
                    };
                };
            });
        });
        language_source.on('change', language_source, function () {
            bible_source.children('option:not(:first)').remove();
            bible_source.parent().hide();
            submit.hide()
            var lang = language_source.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_source.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_source.parent().show();};
                };
            });
        });
        if (bible_source.length >= 1) {
            bible_source.on('change', bible_source, function () {
                if ($(this).val() || 0){
                    submit.show();
                } else {
                    submit.hide();
                }
            });
        }
    }

//SOURCE MENU

    if ($('.o_source_menu').length) {
        $('.o_source_menu').ready(function(){
            $("div[id='show_source_button'] a").text("Show Source");
            $("div[id='hide_source_button'] a").text("Hide Source");
            $("div[id='source_menu']").show()
        });
    }

//EDITOR MENU

    if ($('.o_edit_mode').length) {
        $('.o_edit_mode').ready(function(){
            $("div[id='show_button'] a").text("Edit Mode");
            $("div[id='hide_button'] a").text("View Mode");
            $("div[id='editor_menu']").show()
        });
    }

    if ($('.o_editor').length) {
        $('.o_editor').on('click', "a[name='switch_show']", function () {
            $("a[name='switch_show']").parent().hide();
            $("a[name='switch_hide']").parent().show();
            $("div[name='show_items']").show();
            $("tr[name='show_items']").show();
            $("td[name='show_items']").show();
            $("th[name='show_items']").show();
            $("span[name='show_items']").show();
            $("a[name='show_items']").show();
            $("a[name='hide_items']").hide();
            $("span[name='hide_items']").hide();
            $("td[name='hide_items']").hide();
            });
        $('.o_editor').on('click', "a[name='switch_hide']", function () {
            $("a[name='switch_show']").parent().show();
            $("a[name='switch_hide']").parent().hide();
            $("div[name='show_items']").hide();
            $("tr[name='show_items']").hide();
            $("td[name='show_items']").hide();
            $("th[name='show_items']").hide();
            $("span[name='show_items']").hide();
            $("a[name='show_items']").hide();
            $("a[name='hide_items']").show();
            $("span[name='hide_items']").show();
            $("td[name='hide_items']").show();
            });
        $('.o_editor').on('click', "a[name='show_source']", function () {
            $("a[name='show_source']").parent().hide();
            $("a[name='hide_source']").parent().show();
            $("div[name='source_item']").show();
            $("tr[name='source_item']").show();
            $("td[name='source_item']").show();
            });
        $('.o_editor').on('click', "a[name='hide_source']", function () {
            $("a[name='show_source']").parent().show();
            $("a[name='hide_source']").parent().hide();
            $("div[name='source_item']").hide();
            $("tr[name='source_item']").hide();
            $("td[name='source_item']").hide();
            });
    }


//    TEXT AREA

    $('textarea.load_editor').each(function () {
        var $textarea = $(this);
        var editor_karma = $textarea.data('karma') || 30;  // default value for backward compatibility
        if (!$textarea.val().match(/\S/)) {
            $textarea.val("<p><br/></p>");
        }
        var $form = $textarea.closest('form');
        var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['history', ['undo', 'redo']],
            ];
        if (parseInt($("#karma").val()) >= editor_karma) {
            toolbar.push(['insert', ['link', 'picture']]);
        }
        $textarea.summernote({
                height: 150,
                toolbar: toolbar,
                styleWithSpan: false
            });

        // float-left class messes up the post layout OPW 769721
        $form.find('.note-editable').find('img.float-left').removeClass('float-left');
        $form.on('click', 'button, .a-submit', function () {
            $textarea.html($form.find('.note-editable').code());
        });
    });


//    DICTIONARY

    if ($('.o_word').length) {
        var get_dictionary = function () {
            var word = $("input[name='the_word']").val();
            var lang = $("select[name='select_language']").val();
            var dict_place = $("div[name='dictionaries']");
            ajax.jsonRpc('/get/dictionary', 'call', {
                word_id: word,
                lang_id: lang,
                }).then(function (data) {
                    dict_place.children().remove();
                    if (data.length > 0){
                        var i;
                        for (i = 0; i < data.length; i++) {
                            dict_place.append('<h5>' + data[i].name + '</h5>')
                        };
                    };
                });
            };

        var add_dictionary = function () {
            var word = $("input[name='the_word']").val();
            var lang = $("select[name='select_language']").val();
            var dict = $("input[name='word_dictionary']").val();
            ajax.jsonRpc('/add/dictionary', 'call', {
                word_id: word,
                lang_id: lang,
                dict_id: dict,
                }).then(function (data) {
                    $("input[name='word_dictionary']").val(null);
                    get_dictionary();
                });
            };

        $('.o_word').ready(function(){
            get_dictionary();
        });
        $("select[name='select_language']").on('change', function () {
            get_dictionary();
        });
        $("a[name='add_dict']").on('click', function () {
            add_dictionary();
        });
        $("input[name='word_dictionary']").keypress(function( event ) {
          if ( event.which == 13 ) {
            add_dictionary();
          }
        });
    }

//    TRANSLATE CONTENT

    if ($('.o_trans_content').length) {
        var content_options = $("select[name='content_id']:enabled option:not(:first)");
        $('.o_trans_content').on('change', "select[name='biblica_id']", function () {
            var select = $("select[name='content_id']");
            content_options.detach();
            var displayed_content = content_options.filter("[data-biblica_id="+($(this).val() || 0)+"]");
            var nb = displayed_content.appendTo(select).show().size();
            select.parent().toggle(nb>=1);
            if (nb>=1) {
                $("div[id='new_content']").show();
                $("div[id='new_biblica']").hide();
            } else {
                $("div[id='new_content']").show();
                $("div[id='new_biblica']").show();
            }
        });
        $('.o_trans_content').on('click', "select[name='content_id']", function () {
            if ($(this).val() || 0){
                    $("div[id='new_content']").hide();
                    $("div[id='new_biblica']").hide();
            } else {
                    $("div[id='new_content']").show();
                    $("div[id='new_biblica']").hide();
            }
        });
        $('.o_trans_content').find("select[name='biblica_id']").change();
        $('.o_trans_content').find("select[name='content_id']").change();
    }

//SOURCING MENU

    if ($('.o_sourcing_b').length) {
        var submit_sourcing_b = function () {
            var biblica = $("input[name='biblica_id']").val();
            var content = $("input[name='content_id']").val();
            var s_part = $("input[name='s_part_id']").val();
            ajax.jsonRpc('/submit/sourcing/', 'call', {
                biblica_id: biblica,
                content_id: content,
                s_part_id: s_part,
                }).then(function (data) {
                    if (data.s_part_id != null){
                        $("h2[id='report']").empty().text(data.s_part_id);
                        $("input[name='biblica_id']").val(data.biblica_id);
                        $("input[name='content_id']").val(data.content_id);
                        $("input[name='s_part_id']").val(data.s_part_id);
                        submit_sourcing_b();
                    } else if (data.biblica_id != null) {
                    self.location = "/biblica/" + data.biblica_id;
                    } else if (data.content_id != null) {
                    self.location = "/content/" + data.content_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_sourcing_b').ready(function(){
            submit_sourcing_b();
        });
    }

    if ($('.o_copying_b').length) {
        var submit_copying_b = function () {
            var biblica = $("input[name='biblica_id']").val();
            var content = $("input[name='content_id']").val();
            var s_part = $("input[name='s_part_id']").val();
            ajax.jsonRpc('/copying/source/', 'call', {
                biblica_id: biblica,
                content_id: content,
                s_part_id: s_part,
                }).then(function (data) {
                    if (data.s_part_id != null){
                        $("h2[id='report']").empty().text(data.s_part_id);
                        $("input[name='biblica_id']").val(data.biblica_id);
                        $("input[name='content_id']").val(data.content_id);
                        $("input[name='s_part_id']").val(data.s_part_id);
                        submit_copying_b();
                    } else if (data.biblica_id != null) {
                    self.location = "/biblica/" + data.biblica_id;
                    } else if (data.content_id != null) {
                    self.location = "/content/" + data.content_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_copying_b').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_remove_source').length) {
        var submit_copying_b = function () {
            var biblica = $("input[name='biblica_id']").val();
            var content = $("input[name='content_id']").val();
            var s_part = $("input[name='s_part_id']").val();
            ajax.jsonRpc('/remove/source/', 'call', {
                biblica_id: biblica,
                content_id: content,
                s_part_id: s_part,
                }).then(function (data) {
                    if (data.s_part_id != null){
                        $("h2[id='report']").empty().text(data.s_part_id);
                        $("input[name='biblica_id']").val(data.biblica_id);
                        $("input[name='content_id']").val(data.content_id);
                        $("input[name='s_part_id']").val(data.s_part_id);
                        submit_copying_b();
                    } else if (data.biblica_id != null) {
                    self.location = "/biblica/" + data.biblica_id;
                    } else if (data.content_id != null) {
                    self.location = "/content/" + data.content_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_remove_source').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_remove').length) {
        var submit_copying_b = function () {
            var biblica = $("input[name='biblica_id']").val();
            var part = $("input[name='part_id']").val();
            ajax.jsonRpc('/remove/p/', 'call', {
                biblica_id: biblica,
                part_id: part,
                }).then(function (data) {
                    if (data.part_id != null){
                        $("h2[id='report']").empty().text(data.part_id);
                        $("input[name='biblica_id']").val(data.biblica_id);
                        $("input[name='part_id']").val(data.part_id);
                        submit_copying_b();
                    } else if (data.biblica_id != null) {
                    self.location = "/biblica/" + data.biblica_id;
                    } else {
                    self.location = "/my/home";
                    }
                });
            };

        $('.o_remove').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_cleaning').length) {
        var submit_copying_b = function () {
            var part = $("input[name='part_id']").val();
            ajax.jsonRpc('/cleaning/p/', 'call', {
                part_id: part,
                }).then(function (data) {
                    if (data.part_id != null){
                        $("h2[id='report']").empty().text(data.part_id);
                        $("input[name='part_id']").val(data.part_id);
                        submit_copying_b();
                    } else {
                        $("#install_next_button").click();
                    }
                });
            };

        $('.o_cleaning').ready(function(){
            submit_copying_b();
        });
    }

});