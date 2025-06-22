document.addEventListener('DOMContentLoaded', function () {
    const searchButton = document.getElementById('search');
    const filtrosContent = document.querySelector('.filtrosContent');

    if (searchButton && filtrosContent) {
        const searchIcon = searchButton.querySelector('i');

        searchButton.addEventListener('click', function () {
            if (filtrosContent.classList.contains('show')) {
                filtrosContent.classList.remove('show');
                setTimeout(() => {
                    filtrosContent.style.display = 'none';
                    searchButton.classList.remove('right');
                    if (searchIcon) {
                        searchIcon.classList.remove('bx-x');
                        setTimeout(() => {
                            searchIcon.classList.add('bx-search');
                        }, 100);
                    }
                }, 300);
            } else {
                filtrosContent.style.display = 'flex';
                setTimeout(() => {
                    filtrosContent.classList.add('show');
                }, 10);
                searchButton.classList.add('right');
                if (searchIcon) {
                    searchIcon.classList.remove('bx-search');
                    searchIcon.classList.add('bx-x');
                }
            }
        });
    }
});