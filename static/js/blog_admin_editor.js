document.addEventListener('DOMContentLoaded', function () {
    var el = document.querySelector('.markdown-editor');
    if (el && typeof EasyMDE !== 'undefined') {
        new EasyMDE({
            element: el,
            spellChecker: false,
            autosave: { enabled: true, uniqueId: 'blog_content', delay: 3000 },
            toolbar: ['bold','italic','heading','|','quote','unordered-list','ordered-list','|','link','image','table','|','preview','side-by-side','fullscreen','|','guide'],
            minHeight: '400px',
        });
    }
});
