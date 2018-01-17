from openerp import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
"""
class StockQuantity(models.Model):
    _inherit = 'stock.quant'
    
    flag = fields.Boolean(default=True)

    @api.constrains('quantity')
    #@api.depends('quantity')
    def _onchange_quantity(self):
        if self.flag:
            self.flag = False
            print ("########## QTY A ##########")
            self.quantity = self.env['sale.order.line']._update_stock_quantity(self)
            print ("########## QTY B ##########")
            print ("########## ", self.quantity," ##########")
            
        self.flag = True
"""
class stock_location(models.Model):
    _inherit = 'stock.location'

    consignee_id = fields.Many2one('res.partner','Consignee', readonly=True)
    is_consignment = fields.Boolean('Consignment Location', readonly=True)


    @api.one
    @api.constrains('consignee_id')
    def _check_internal_location(self):
        if self.consignee_id and self.usage != 'internal':
            raise Warning(_('A consignee Location must be always internal'))


class StockMoves(models.Model):
    _inherit = 'stock.move'
    #_inherit = 'stock.move.line'
    
#---
    
    #############
    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        rec = super(StockMoves, self)._prepare_move_line_vals(quantity=None, reserved_quant=None)
            
        print ("########## OVERRIDDEN METHOD START ##########")
        #
        print ("########## - A - ##########")
        #
        src_loc_id = ''
        dest_loc_id = ''
        #
        print ("########## - B - ##########")
        #
        if self.sale_line_id.order_id.order_type == 'con_order':
            dest_loc_id = self.sale_line_id.order_id.partner_id.consignee_location_id.id
            #
            print ("########## - C - ##########")
            #
        elif self.sale_line_id.order_id.order_type == 'con_sale':
            src_loc_id = self.sale_line_id.order_id.partner_id.consignee_location_id.id,
            #
            print ("########## - D - ##########")
            #
        self.ensure_one()
        # apply putaway
        location_dest_id = self.location_dest_id.get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': src_loc_id or self.location_id.id,
            #'location_dest_id': dest_loc_id or location_dest_id,
            'location_dest_id': dest_loc_id,
            'picking_id': self.picking_id.id,
        }
        if quantity:
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            vals = dict(vals, product_uom_qty=uom_quantity)
        if reserved_quant:
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        print ("########## ", location_dest_id, " ##########")
        print ("########## ", src_loc_id, " ##########")
        print ("########## ", dest_loc_id, " ##########")
        print ("########## OVERRIDDEN METHOD ENDS ##########")
        return vals
        return rec
    #############
    
    
"""
    @api.model
    def create(self, vals):
        rec = super(StockMoves, self).create(vals)
        vals['ordered_qty'] = vals.get('product_uom_qty')
        if 'picking_id' in vals and 'move_id' not in vals:
            picking2 = self.env['stock.picking'].browse(vals['picking_id'])
            #
            print ("########## - A - ##########")
            #
            src_loc_id = ''
            dest_loc_id = ''
            #
            print ("########## - B - ##########")
            #
            if self.move_id.sale_line_id.order_id.order_type == 'con_order':
                src_loc_id = self.move_id.sale_line_id.order_id.partner_id.consignee_location_id.id
                #
                print ("########## - C - ##########")
                #
            elif self.move_id.sale_line_id.order_id.order_type == 'con_sale':
                dest_loc_id = self.move_id.sale_line_id.order_id.partner_id.consignee_location_id.id,
                #
                print ("########## - D - ##########")
                #
            if picking2.state == 'done':
                product = self.env['product.product'].browse(vals['product_id'])
                new_move = self.env['stock.move'].create({
                    'name': _('New Move:') + product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': 'qty_done' in vals and vals['qty_done'] or 0,
                    'product_uom': vals['product_uom_id'],
                    #'location_id': 'location_id' in vals and vals['location_id'] or picking.location_id.id,
                    #'location_dest_id': 'location_dest_id' in vals and vals['location_dest_id'] or picking.location_dest_id.id,
                    'location_id': src_loc_id,
                    'location_dest_id': dest_loc_id,
                    'state': 'done',
                    'additional': True,
                    'picking_id': picking2.id,
                })
                vals['move_id'] = new_move.id
                #
                print ("########## - E - ##########")
                #
"""
"""
        ml = super(StockMoves, self).create(vals)
        if ml.state == 'done':
            if ml.product_id.type == 'product':
                Quant = self.env['stock.quant']
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,rounding_method='HALF-UP')
                in_date = None
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            next_moves = ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
            next_moves._do_unreserve()
            next_moves._action_assign()
        return ml
        
        return rec
        #
"""
"""
        class AccountJournal(models.Model):
        _inherit = "account.journal"

        @api.model
        def create(self, vals):
        rec = super(AccountJournal, self).create(vals)
        # ...        
        return rec
"""
#---
"""
    def _run_move_create(self):
        print ("OVERRIDDEN METHOD------------------------------")
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        print ("_run_move_create-----------procurement-----",procurement)
        newdate = (datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.rule_id.delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
        group_id = False
        if procurement.rule_id.group_propagation_option == 'propagate':
            group_id = procurement.group_id and procurement.group_id.id or False
        elif procurement.rule_id.group_propagation_option == 'fixed':
            group_id = procurement.rule_id.group_id and procurement.rule_id.group_id.id or False
        #it is possible that we've already got some move done, so check for the done qty and create
        #a new move with the correct qty
        already_done_qty = 0
        already_done_qty_uos = 0
        for move in procurement.move_ids:
            already_done_qty += move.product_uom_qty if move.state == 'done' else 0
            already_done_qty_uos += move.product_uos_qty if move.state == 'done' else 0
        qty_left = max(procurement.product_qty - already_done_qty, 0)
        qty_uos_left = max(procurement.product_uos_qty - already_done_qty_uos, 0)
        # INHERITED PART START
        src_loc_id = procurement.rule_id.location_src_id.id
        dest_loc_id = procurement.location_id.id
        if procurement.sale_line_id.order_id.order_type == 'con_order':
                # change the dest loc to consignee loc, as we are moving stock to consignee loc
                dest_loc_id = procurement.sale_line_id.order_id.partner_id.consignee_location_id.id
        elif procurement.sale_line_id.order_id.order_type == 'con_sale':
                # change the source loc to consignee loc, as this is the stock to be moved to customer from consignment loc
                src_loc_id = procurement.sale_line_id.order_id.partner_id.consignee_location_id.id
        # INHERITED PART END
        vals = {
            'name': procurement.name,
            'company_id': procurement.rule_id.company_id.id or procurement.rule_id.location_src_id.company_id.id or procurement.rule_id.location_id.company_id.id or procurement.company_id.id,
            'product_id': procurement.product_id.id,
            'product_uom': procurement.product_uom.id,
            'product_uom_qty': qty_left,
            'product_uos_qty': (procurement.product_uos and qty_uos_left) or qty_left,
            'product_uos': (procurement.product_uos and procurement.product_uos.id) or procurement.product_uom.id,
            'partner_id': procurement.rule_id.partner_address_id.id or (procurement.group_id and procurement.group_id.partner_id.id) or False,
            'location_id': src_loc_id,
            'location_dest_id': dest_loc_id,
            'move_dest_id': procurement.move_dest_id and procurement.move_dest_id.id or False,
            'procurement_id': procurement.id,
            'rule_id': procurement.rule_id.id,
            'procure_method': procurement.rule_id.procure_method,
            'origin': procurement.origin,
            'picking_type_id': procurement.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, x.id) for x in procurement.route_ids],
            'warehouse_id': procurement.rule_id.propagate_warehouse_id.id or procurement.rule_id.warehouse_id.id,
            'date': newdate,
            'date_expected': newdate,
            'propagate': procurement.rule_id.propagate,
            'priority': procurement.priority,
        }
        return vals
    """