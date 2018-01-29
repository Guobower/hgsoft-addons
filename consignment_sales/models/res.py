# -*- coding: utf-8 -*-

import io
import xlsxwriter
from odoo import models, fields, api
import base64
from datetime import datetime

class res_partner(models.Model):
    _inherit = 'res.partner'

    allow_consignment = fields.Boolean("Permite Consignação")

    is_author = fields.Boolean("Autor", default=False)

    consignee_location_id = fields.Many2one('stock.location','Local de Consignação')

    report_attachment_ids = fields.One2many('ir.attachment','consignment_partner_id',string='Relatórios de Consignação')

    send_auto_email = fields.Boolean("Enviar Relatório Automático")

    @api.multi
    def create_consignee_location(self):
        location_obj = self.env['stock.location']

        default_vals = location_obj.default_get(location_obj.fields_get())

        location_vals = {'usage':'internal',
                         'name': self.name+' - Local de Consignação',
                         'consignee_id': self.id,
                         'is_consignment': True
                        }
        default_vals.update(location_vals)

        location_id = location_obj.create(default_vals)

        self.consignee_location_id = location_id.id

    @api.model
    def create(self, vals):
        partner = super(res_partner, self).create(vals)

        if vals.get('allow_consignment'):
            print (partner.create_consignee_location())
        return partner

    @api.multi
    def write(self, vals):
        if vals.get('allow_consignment'):
            # Create consignent location for this customer if not present.
            con_loc_exists = self.env['stock.location'].search([('consignee_id','=', self.id),('usage','=','internal')], limit=1)
            if not con_loc_exists:
                self.create_consignee_location()
        partner = super(res_partner, self).write(vals)
        return partner

    
    @api.multi
    def action_view_consignment_products(self):
        self.ensure_one()
        
        imd = self.env['ir.model.data']
        
        list_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_tree')
        
        form_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_form')
        
        action = self.env.ref('consignment_sales.consignee_open_quants').read()[0]
        
        action['domain'] = "[('location_id','=',%s)]" % self.consignee_location_id.id
        
        action['context'] = {'search_default_internal_loc': 1, 'search_default_productgroup': 1}
        
        action['views'] = [[list_view_id, 'tree'], [form_view_id, 'form']]
        
        return action

    @api.multi
    def create_xls_consignment_report(self):
        #This method will Generate the XLS file with the specified columns, 
        # and save it in a new attachment 
        print ("##### create_xls_consignment_report [START] #####")
        
        consignent_location = self.consignee_location_id
        
        if not consignent_location:
            return False
        
        # Fetch the stock at this customer's consignee location
        consignment_quants = self.env['stock.quant'].search([('location_id','=',consignent_location.id)])
        
        line_data = []
        for each_quant in consignment_quants:
            if each_quant.product_id in [x['product_id'] for x in line_data]:
                for each_data in line_data:
                    if each_data['product_id'] == each_quant.product_id:
                        each_data['quantity'] += each_quant.quantity
            else:
                line_data.append({'product_id': each_quant.product_id, 'quantity': each_quant.quantity})

        # Now we have product and its qty, so we now fetch sale price and discounted price by help of pricelists
        pricelist = self.property_product_pricelist
        for each_prd in line_data:
            pricelist_price = pricelist.price_get(each_prd['product_id'].id, each_prd['quantity'], partner=self.id)
            
            if pricelist_price and pricelist_price.get(pricelist.id):
                each_prd['cost_price'] = pricelist_price[pricelist.id]
                
                each_prd['sale_price'] = each_prd['product_id'].list_price
                
                # discount will be incorrect if, sale_price is 0
                each_prd['discount'] = (1 - (each_prd['cost_price']/(each_prd['sale_price'] or 1)))*100.00
                
                each_prd['total'] = each_prd['cost_price'] * each_prd['quantity']

        output = io.BytesIO()
        
        workbook = xlsxwriter.Workbook(output, {'in_memory':True})
        
        worksheet = workbook.add_worksheet()
        
        # Customer Details at top rows
        worksheet.write(0,0,self.company_id.name)
        worksheet.write(1,0,self.company_id.email)
        worksheet.write(1,2,self.company_id.phone)
        worksheet.write(3,0,self.name)
        
        #TODO: 
        worksheet.write(5,0,datetime.now().strftime('%Y-%m-%d'))
        worksheet.write(7,7,'* Preencher e devolver')
        worksheet.write(8,0,"ISBN")
        worksheet.write(8,1,"Título")
        worksheet.write(8,2,"Qde")
        worksheet.write(8,3,"Desc.")
        worksheet.write(8,4,"Valor c/ desc.")
        worksheet.write(8,5,"Valor")
        worksheet.write(8,6,"Total")
        worksheet.write(8,7,"Acerto")
        worksheet.write(8,8,u"Reposição*")
    
        for each_row in range(9,len(line_data)+9):
            worksheet.write(each_row,0,line_data[each_row-9]['product_id'].ean13)
            worksheet.write(each_row,1,line_data[each_row-9]['product_id'].name)
            worksheet.write(each_row,2,line_data[each_row-9]['quantity'])
            worksheet.write(each_row,3,line_data[each_row-9]['discount'])
            worksheet.write(each_row,4,line_data[each_row-9]['cost_price'])
            worksheet.write(each_row,5,line_data[each_row-9]['sale_price'])
            worksheet.write(each_row,6,line_data[each_row-9]['total'] )
        workbook.close()

        file_data = base64.b64encode(output.getvalue())
        
        mode = 'manual'
        if self._context.get('mode') and self._context.get('mode') == 'auto':
            mode = 'auto'
        
        attachment_vals = {'name': u'Relatório de Consignação.xlsx', 'res_model': 'mail.compose.message',
                           'res_id': 0, 'datas_fname': u'Relatório de Consignação', 
                           'type': 'binary', 'datas': file_data, 'consignment_partner_id': self.id,
                           'consignment_mode': mode}
        attachment_id = self.env['ir.attachment'].create(attachment_vals)
        
        print ("##### create_xls_consignment_report [END]] #####")
        
        return attachment_id.id
    
    @api.model
    def consignment_report_cron(self):
        print ("##### consignment_report_cron [START] #####")
        
        customers = self.search([('send_auto_email','=',True)])
        
        template_id = self.env['ir.model.data'].get_object_reference('consignment_sales',
                                                                     'email_template_partner_consignment_report')[1]
        for each_cst in customers:
            attachment_id = each_cst.with_context({'mode':'auto'}).create_xls_consignment_report()
        
            self.env['mail.template'].browse(template_id).send_mail(each_cst.id)
        
        print ("##### consignment_report_cron [END] #####")
            
class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        result = super(mail_compose_message, self).default_get(fields)

        consignment_template = self.env.ref("consignment_sales.email_template_partner_consignment_report")

        if result.get('template_id') and result.get('template_id') == consignment_template.id:
            if self._context and self._context.get('active_id'):
                attachment_id = self.env['res.partner'].browse(self._context.get('active_id')).create_xls_consignment_report()

                if attachment_id:
                    result['attachment_ids'] = [attachment_id]

        return result

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    consignment_partner_id = fields.Many2one('res.partner','Relatório para:', readonly=True)
    
    consignment_mode = fields.Selection([('auto','Automatic'),('manual','Manual')], string="Modo de Criação")
    
    @api.model
    def create(self, vals):
        attach = super(ir_attachment, self).create(vals)

        return attach