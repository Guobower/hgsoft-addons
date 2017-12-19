# -*- coding: utf-8 -*-
    
    #Documentation
    #This 'model' adds new fields to 'product.template'.
    #'product.template' is the main Product model.

from odoo import tools
from odoo import models, fields, api

class RoyaltiesReport(models.Model):
    #_inherit = ['sale.report', 'sale.order']  
    _inherit = 'sale.report' 
    _auto = False
    #_name = 'sale.report'
    _name = 'royalties.report'
    
    #class SaleReport(osv.osv):
    #_inherit = 'sale.report'

    #_columns = {
    #    'royalties_to_pay': fields.Float('Royalties to Pay', readonly=True),
    #    'royalties_percentage': fields.Many2one('res.partner', "Percentage of Royalties", readonly=True)
    #}
    
    #Class inheritance
    
    #_inherit = ['sale.report', 'sale.order']
    
    royalties_percentage = fields.Many2one('res.partner', string="Percentage of Royalties", readonly=True)
    
    royalties_to_pay = fields.Many2one('res.partner', string="Royalties to Pay", readonly=True)

    #royalties_to_pay = fields.Float('Royalties to Pay', readonly=True)
    
    #@api.model_cr
    #def init(self):
    # super(RoyaltiesReport,self).init()
    #    #self._table = royalties_report
    #    tools.drop_view_if_exists(self.env.cr, self._table)
    #    self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
    #        %s
    #        FROM ( %s )
    #        %s
    #        )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _group_by(self):
        return super(RoyaltiesReport,self)._group_by() + ', royalties_to_pay'
    
 #   def _select(self):
 #       return super(RoyaltiesReport,self)._select() + ', partner.royalties_to_pay as royalties_to_pay'

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    sum(l.amt_to_invoice / COALESCE(cr.rate, 1.0)) as amt_to_invoice,
                    sum(l.amt_invoiced / COALESCE(cr.rate, 1.0)) as amt_invoiced,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.confirmation_date as confirmation_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.analytic_account_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume,
                    partner.royalties_to_pay as royalties_to_pay
        """ % self.env['res.currency']._select_companies_rates()
        return select_str
    
    def _from(self):
        from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
        return from_str
   
    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, royalties_report)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (royalties_report, self._select(), self._from(), self._group_by()))
   

    #royalties_to_pay = fields.Float(store=True, readonly=True)

    #@api.multi    
    #@api.depends('price_total', 'royalties_percentage')
    #@api.onchange('amount', 'unit_price')
    #@api.constrains('royalties_percentage')
    #def _compute_royalties(self):
     #   self.royalties_to_pay = self.price_total * (self.royalties_percentage.royalties_percentage / 100.0)
        #for r in self:
        #    if not r.royalties_percentage:
        #        r.royalties_to_pay = 0.0
        #    else:
        #        r.royalties_to_pay = price_total * (royalties_percentage / 100.0)