//    SUB CONTENT
    var get_subcontent = function () {
        var content = $("input[name='content_id']").val();
        var subcontent_place = $("div[name='subcontent']");
        ajax.jsonRpc('/get/subcontent', 'call', {
            content_id: content,
            }).then(function (data) {
            subcontent_place.children().remove();
            subcontent_place.append('<table>');
            if (data.length > 0){
                var i;
                for (i = 0; i < data.length; i++) {
                    subcontent_place.append(
                    '<tr class="o_subcontent_chapter"><td>' +
                    '<div name="subcontent_chapter"/><h5>' +
                    data[i].name + '</h5>' +
//                        '<a role="button" class="btn btn-sm btn-link" href="/subcontent/' +
//                        data[i].name + '-' + data[i].id +
//                        '">' + data[i].name + '</a></td>' +
                    '<input type="hidden" name="subcontent_id" t-att-value="' + data[i].id + '"/>' +
                    '<td t-if="biblica_id.create_id == user_id">' +
                            ' <input type="text" name="chapter" required="True"/>' +
                            ' <a role="button" href="#" name="add_subcontent_chapter" class="btn btn-primary btn-sm">Add new chapter</a>' +
                    '</td></tr>'
                    );
                };
            };
            subcontent_place.append('</table>');
        });
    };

    if ($('.o_subcontent').length) {
        $('.o_subcontent').ready(function(){
            get_subcontent();
        });
        $("a[name='add_subcontent']").on('click', function () {
            var content = $("input[name='content_id']").val();
            var csrf = $("input[name='csrf_token']").val();
            var title = $("input[name='subcontent_text']").val();
            ajax.jsonRpc('/add/subcontent', 'call', {
                content_id: content,
                csrf_token: csrf,
                name: title,
                }).then(function (data) {
                get_subcontent();
                $("input[name='subcontent_text']").val(null);
            });
        });
    }

//    CHAPTER

    var get_chapter = function () {
        var content = $("input[name='content_id']").val();
        var chapter_place = $("div[name='chapter']");
        ajax.jsonRpc('/get/chapter', 'call', {
            content_id: content,
            }).then(function (data) {
            chapter_place.children().remove();
            if (data.length > 0){
                var i;
                for (i = 0; i < data.length; i++) {
                    chapter_place.append(
                    '<li><a role="button" class="btn btn-sm btn-link" href="/part/' + data[i].name + '-' + data[i].id +
                    '"><h5>Chapter ' + data[i].name + '</h5></a>' +
                    '<div name="show_items" style="display:none;" class="mb16" t-if="biblica_id.create_id == user_id">' +
                    '<form id="edit_part" t-attf-action="/edit/part" method="post" role="form" class="tag_text js_website_submit_form">' +
                        '<input type="text" name="name" required="True"/>' +
                        '<button type="submit" class="btn btn-warning btn-sm mt8">Edit</button>' +
                        '<a role="button" href="/remove/part/' + data[i].name + '-' + data[i].id + '" class="btn btn-sm btn-danger mt8">Remove</a>' +
                        '<a role="button" href="/up/part/' + data[i].name + '-' + data[i].id + '" class="btn btn-sm btn-primary mt8">Up</a>' +
                        '<a role="button" href="/down/part/' + data[i].name + '-' + data[i].id + '" class="btn btn-sm btn-primary mt8">Down</a>' +
                    '</form></div></li>'
                    );
                };
            };
        });
    };

    if ($('.o_chapter').length) {
        $('.o_chapter').ready(function(){
            get_chapter();
        });
        $("a[name='add_chapter']").on('click', function () {
            var content = $("input[name='content_id']").val();
            var csrf = $("input[name='csrf_token']").val();
            var title = $("input[name='chapter_text']").val();
            ajax.jsonRpc('/add/chapter', 'call', {
                content_id: content,
                csrf_token: csrf,
                name: title,
                }).then(function (data) {
                get_chapter();
                $("input[name='chapter_text']").val(null);
            });
        });
    }

