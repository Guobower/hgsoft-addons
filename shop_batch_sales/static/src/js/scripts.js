odoo.define('website_sale.tracking', function(require) {

var ajax = require('web.ajax');

$(document).ready(function () {

    // Watching a product
    if ($("#product_detail.oe_website_sale").length) {
        var prod_id = $("input[name='product_id']").attr('value');
        vpv("/stats/ecom/product_view/" + prod_id);
        alert("Watch");
        alert(prod_id);
    }

    // Add a product into the cart
    $(".oe_website_sale form[action='/shop/cart/update'] a.a-submit2").on('click', function(o) {
        var prod_id = $("input[name='product_id']").attr('value');
        vpv("/stats/ecom/product_add_to_cart/" + prod_id);
        alert("Add");
        alert(prod_id);
    });
    
    //===============
    //    var prod_ids = (""+(prod_id.match(/\d+/g))).split(",");
    //    for (var x in prod_ids) {
    //    vpv("/stats/ecom/product_add_to_cart/" + x);
    //    vpv("/stats/ecom/product_add_to_cart/" + "61");
    // }
    //===============

    // Start checkout
    $(".oe_website_sale a[href='/shop/checkout']").on('click', function(o) {
        vpv("/stats/ecom/customer_checkout");
        alert("A");
    });

    $(".oe_website_sale div.oe_cart a[href^='/web?redirect'][href$='/shop/checkout']").on('click', function(o) {
        vpv("/stats/ecom/customer_signin");
        alert("B");
    });

    $(".oe_website_sale form[action='/shop/confirm_order'] a.a-submit").on('click', function(o) {
        if ($("#top_menu > li > a[href='/web/login']").length){
            vpv("/stats/ecom/customer_signup");
        }
        vpv("/stats/ecom/order_checkout");
        alert("C");
    });

    $(".oe_website_sale form[target='_self'] button[type=submit]").on('click', function(o) {
        var method = $("#payment_method input[name=acquirer]:checked").nextAll("span:first").text();
        vpv("/stats/ecom/order_payment/" + method);
        alert("D");
    });

    if ($(".oe_website_sale div.oe_website_sale_tx_status").length) {
        track_ga('require', 'ecommerce');

        var order_id = $(".oe_website_sale div.oe_website_sale_tx_status").data("order-id");
        vpv("/stats/ecom/order_confirmed/" + order_id);
        alert("E");
        ajax.jsonRpc("/shop/tracking_last_order/").then(function(o) {
            track_ga('ecommerce:clear');

            if (o.transaction && o.lines) {
                track_ga('ecommerce:addTransaction', o.transaction);
                _.forEach(o.lines, function(line) {
                    track_ga('ecommerce:addItem', line);
                });
            }
            track_ga('ecommerce:send');
        });
    }

    function vpv(page){ //virtual page view
        track_ga('send', 'pageview', {
          'page': page,
          'title': document.title,
        });
    }

    function track_ga() {
        website_ga = this.ga || function(){};
        website_ga.apply(this, arguments);
    }

});

});
