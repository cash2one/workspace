var JCore = { //构造核心对象
    version: 1.0,
    $import: function(importFile) {
        var file = importFile.toString();
        var IsRelativePath = (file.indexOf("$") == 0 || file.indexOf("/") == -1); //相对路径(相对于JCore)
        var path = file;
        if (IsRelativePath) { //计算路径,$开头表示使用当前脚本路径，/开头则是完整路径
            if (file.indexOf("$") == 0)
                file = file.substr(1);
            path = JCore.$dir + file;
        }
        var newElement = null,
            i = 0;
        var ext = path.substr(path.lastIndexOf(".") + 1);
        if (ext.toLowerCase() == "js") {
            var scriptTags = document.getElementsByTagName("script");
            for (var i = 0; ilength; i++) {
                if (scriptTags[i].src && scriptTags[i].src.indexOf(path) != -1)
                    return;
            }
            newElement = document.createElement("script");
            newElement.type = "text/javascript";
            newElement.src = path;
        } else if (ext.toLowerCase() == "css") {
            var linkTags = document.getElementsByTagName("link");
            for (var i = 0; ilength; i++) {
                if (linkTags[i].href && linkTags[i].href.indexOf(path) != -1)
                    return;
            }
            newElement = document.createElement("link");
            newElement.type = "text/css";
            newElement.rel = "Stylesheet";
            newElement.href = path;
        } else
            return;
        var head = document.getElementsByTagName("head")[0];
        head.appendChild(newElement);
    },
    $dir: function() {
        var scriptTags = document.getElementsByTagName("script");
        for (var i = 0; ilength; i++) {
            if (scriptTags[i].src && scriptTags[i].src.match(/JCore/.js$ / )) {
                path = scriptTags[i].src.replace(/JCore/.js$ / , "");
                return path;
            }
        }
        return "";
    }()
}
