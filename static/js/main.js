function render_tag_buttons(object) {
    var els = object.getElementsByClassName('tags');
    for (var i = 0; i < els.length; ++i) {
        var html = [];
        var items = els[i].innerHTML.split(',');
        for (var j = 0; j < items.length; ++j) {
            var item = items[j];
            while (item[0] == ' ' || item[0] == '\n') {
                item = item.substr(1);
            }
            var l = item.length - 1;
            while (item[l] == ' ' || item[l] == '\n') {
                item = item.substr(0, l--);
            }
            html.push('<a href="/t/');
            html.push(item);
            html.push('" class="tag">');
            html.push(item);
            html.push('</a>');
        }
        els[i].innerHTML = html.join('');
    }
}
SyntaxHighlighter.autoloader(
    'applescript			/static/lib/syntax/scripts/shBrushAppleScript.js',
    'actionscript3 as3		/static/lib/syntax/scripts/shBrushAS3.js',
    'bash shell				/static/lib/syntax/scripts/shBrushBash.js',
    'coldfusion cf			/static/lib/syntax/scripts/shBrushColdFusion.js',
    'cpp c					/static/lib/syntax/scripts/shBrushCpp.js',
    'c# c-sharp csharp		/static/lib/syntax/scripts/shBrushCSharp.js',
    'css					/static/lib/syntax/scripts/shBrushCss.js',
    'delphi pascal			/static/lib/syntax/scripts/shBrushDelphi.js',
    'diff patch pas			/static/lib/syntax/scripts/shBrushDiff.js',
    'erl erlang				/static/lib/syntax/scripts/shBrushErlang.js',
    'groovy					/static/lib/syntax/scripts/shBrushGroovy.js',
    'java					/static/lib/syntax/scripts/shBrushJava.js',
    'jfx javafx				/static/lib/syntax/scripts/shBrushJavaFX.js',
    'js jscript javascript	/static/lib/syntax/scripts/shBrushJScript.js',
    'perl pl				/static/lib/syntax/scripts/shBrushPerl.js',
    'php					/static/lib/syntax/scripts/shBrushPhp.js',
    'text plain				/static/lib/syntax/scripts/shBrushPlain.js',
    'py python				/static/lib/syntax/scripts/shBrushPython.js',
    'ruby rails ror rb		/static/lib/syntax/scripts/shBrushRuby.js',
    'scala					/static/lib/syntax/scripts/shBrushScala.js',
    'sql					/static/lib/syntax/scripts/shBrushSql.js',
    'vb vbnet				/static/lib/syntax/scripts/shBrushVb.js',
    'xml xhtml xslt html	/static/lib/syntax/scripts/shBrushXml.js'
);
SyntaxHighlighter.all();
window.onload = function () {
    render_tag_buttons(document);
};
// fix line wrap issues
(function () {
    var wrap = function () {
        var elems = document.getElementsByClassName('syntaxhighlighter');
        for (var j = 0; j < elems.length; ++j) {
            var sh = elems[j];
            var gLines = sh.getElementsByClassName('gutter')[0].getElementsByClassName('line');
            var cLines = sh.getElementsByClassName('code')[0].getElementsByClassName('line');
            var stand = 15;
            for (var i = 0; i < gLines.length; ++i) {
                var h = $(cLines[i]).height();
                if (h != stand) {
                    console.log(i);
                    gLines[i].setAttribute('style', 'height: ' + h + 'px !important;');
                }
            }
        }
    };
    var waitTillReady = function () {
        if ($('.syntaxhighlighter').length === 0) {
            setTimeout(waitTillReady, 800);
        } else {
            wrap();
        }
    };
    waitTillReady();
})();
function runSearch () {
    window.open('http://google.com/search?q=' + document.searchForm.q.value + ' site:putsnip.com', '_blank');
    return false;
}