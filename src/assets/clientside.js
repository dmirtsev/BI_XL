window.clientside = {
    print_page: function(n_clicks) {
        if (n_clicks > 0) {
            window.print();
        }
        return "Экспорт в PDF";
    }
}
