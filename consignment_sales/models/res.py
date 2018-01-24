# -*- coding: utf-8 -*-

#from StringIO import StringIO
import io
import xlsxwriter
from odoo import models, fields, api
#import shutil
import base64
from datetime import datetime

class res_partner(models.Model):
    _inherit = 'res.partner'

    allow_consignment = fields.Boolean("Allow Consignments")
    is_author = fields.Boolean("Author", default=False)
    consignee_location_id = fields.Many2one('stock.location','Consignment Location')
    report_attachment_ids = fields.One2many('ir.attachment','consignment_partner_id',string='Consignment Reports')
    send_auto_email = fields.Boolean("Send Auto Report")

    @api.multi
    def create_consignee_location(self):
        location_obj = self.env['stock.location']
        default_vals = location_obj.default_get(location_obj.fields_get())
        location_vals = {'usage':'internal',
                         'name': self.name+' Consignee Location',
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

    """
    @api.multi
    def action_view_consignment_products(self):
        print("{:=^20}".format("A"))
        
        # invoice_ids = self.mapped('invoice_ids')
        imd = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        print("{:=^20}".format("B"))
    
        action_id = imd.xmlid_to_res_id('consignment_sales.consignee_open_quants')
        action = act_obj.browse(action_id)
        list_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_tree')
        form_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            # 'target': action.target,

            'context': {'search_default_locationgroup': 1, 'search_default_internal_loc': 1, 'search_default_productgroup': 1},
            # 'domain': {''}
            'res_model': action.res_model,
            'domain': "[('location_id','=',%s)]" % self.consignee_location_id.id
        }
        print("{:=^20}".format("C"))

        return result
    """
    
    @api.multi
    def action_view_consignment_products(self):
        self.ensure_one()
        
        imd = self.env['ir.model.data']
        list_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_tree')
        form_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_form')
        
        action = self.env.ref('consignment_sales.consignee_open_quants').read()[0]
        #action['domain'] = literal_eval(action['domain'])
        action['domain'] = "[('location_id','=',%s)]" % self.consignee_location_id.id
        #action['context'] = {'search_default_locationgroup': 1, 'search_default_internal_loc': 1, 'search_default_productgroup': 1}
        action['context'] = {'search_default_internal_loc': 1, 'search_default_productgroup': 1}
        #action['views'] = [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']]
        action['views'] = [[list_view_id, 'tree'], [form_view_id, 'form']]
        #view_mode
        
        #'name': action.name,
        #    'help': action.help,
        #    'type': action.type,
        #    'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
        #    'target': action.target,
        #    'context': {'search_default_locationgroup': 1, 'search_default_internal_loc': 1, 'search_default_productgroup': 1},
            
        print(action)
        return action

    @api.multi
    def create_xls_consignment_report(self):
        print ("create_xls_consignment_report -------",self)
        #This method will Generate the XLS file with the specified columns, 
        # and save it in a new attachment 
        consignent_location = self.consignee_location_id
        print ("consignent_location-------",consignent_location)
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

        #output = StringIO.StringIO
        print("{:=^20}".format("A"))
        #output = io.StringIO()
        output = io.BytesIO()
    
        print("{:=^20}".format("B"))
        workbook = xlsxwriter.Workbook(output, {'in_memory':True})
        #filename = "Download.xlsx"
        #workbook = xlsxwriter.Workbook(filename, {'in_memory':True})
        worksheet = workbook.add_worksheet()
        
        print("{:=^20}".format("C"))
        # Customer Details at top rows
        worksheet.write(0,0,u"Mapa de consignação da Editora Hedra")
        worksheet.write(1,0,u"comercial@hedra.com.br")
        worksheet.write(1,2,u"11-3097-8304")
        
        print("{:=^20}".format("D"))
        worksheet.write(3,0,self.name)
        #TODO: 
        worksheet.write(5,0,datetime.now().strftime('%Y-%m-%d'))
        worksheet.write(7,7,'* Preencher e devolver')


        print("{:=^20}".format("E"))
        worksheet.write(8,0,"ISBN")
        worksheet.write(8,1,"Titulo")
        worksheet.write(8,2,"Qde")
        worksheet.write(8,3,"Desc.")
        worksheet.write(8,4,"Valor c/ desc.")
        worksheet.write(8,5,"Valor")
        worksheet.write(8,6,"Total")
        worksheet.write(8,7,"Acerto")
        worksheet.write(8,8,u"Reposição*")
    
        print("{:=^20}".format("F"))
        for each_row in range(9,len(line_data)+9):
            worksheet.write(each_row,0,line_data[each_row-9]['product_id'].ean13)
            worksheet.write(each_row,1,line_data[each_row-9]['product_id'].name)
            worksheet.write(each_row,2,line_data[each_row-9]['quantity'])
            worksheet.write(each_row,3,line_data[each_row-9]['discount'])
            worksheet.write(each_row,4,line_data[each_row-9]['cost_price'])
            worksheet.write(each_row,5,line_data[each_row-9]['sale_price'])
            worksheet.write(each_row,6,line_data[each_row-9]['total'] )
        workbook.close()

        # with open ('file.xlsx', 'w') as fd:
        #     output.seek(0)
        #     shutil.copyfileobj(output, fd)
        
        print("{:=^20}".format("G"))
        #
        file_data = base64.b64encode(output.getvalue())
        #file_data = output.getvalue()
        
        print("{:=^20}".format("H"))
        #print("file_data", file_data)
        
        print("{:=^20}".format("I"))
        #print("output getvalue()", output.getvalue())
        
        """
        print("{:=^20}".format("I"))
        file_data_decodeA = base64.b64decode(file_data)
        print("file_data decodeA", file_data_decodeA)

        print("{:=^20}".format("J"))
        file_data_decodeB = base64.b64decode(output.getvalue())
        print("file_data decodeB", file_data_decodeB)
        """
        
        mode = 'manual'
        if self._context.get('mode') and self._context.get('mode') == 'auto':
            mode = 'auto'
        attachment_vals = {'name': u'Consignment Report.xlsx', 'res_model': 'mail.compose.message',
                           'res_id': 0, 'datas_fname': u'Consignment Report', 
                           'type': 'binary', 'datas': file_data, 'consignment_partner_id': self.id,
                           'consignment_mode': mode}
        attachment_id = self.env['ir.attachment'].create(attachment_vals)
        print ("attachment_id-----------",attachment_id)
        return attachment_id.id
    
    #@api.one
    #@api.multi
    @api.model
    def consignment_report_cron(self):
        print ("consignment_report_cron---------------CALLED-------",self)
        customers = self.search([('send_auto_email','=',True)])
        template_id = self.env['ir.model.data'].get_object_reference('consignment_sales',
                                                                     'email_template_partner_consignment_report')[1]
        
        
        print ("template----------", customers)
        
        #email_tmpl_obj = self.env['mail.template']
        
        print("##### FOR EACH #####")
        for each_cst in customers:
            print("##### ATTACHMENT_ID #####")
            attachment_id = each_cst.with_context({'mode':'auto'}).create_xls_consignment_report()
        
            #email_tmpl_obj.send_mail(template_id, each_cst.id, force_send=True)
            
            print("##### EMAIL_TMPL_OBJ #####")
            print("##### ", each_cst.id ," #####")
            print("##### ", each_cst ," #####")
            
            print("##### TEMPLATE_ID #####")
            print("##### ", template_id ," #####")
            
            #email_tmpl_obj.send_mail(template_id, force_send=True, email_values=None)
            self.env['mail.template'].browse(template_id).send_mail(each_cst.id)
            
    """
    #@api.model
    @api.one
    #@api.multi
    def consignment_report_cron(self):
        print ("consignment_report_cron---------------CALLED-------",self)
        customers = self.search([('send_auto_email','=',True)])
        
        #template_id = self.env['ir.model.data'].get_object('consignment_sales', #'email_template_partner_consignment_report')
        
        template_id = self.env['ir.model.data'].get_object_reference('consignment_sales',
        'email_template_partner_consignment_report')[1]
        
        #self.ensure_one() 
        
        print ("template----------",template_id, customers)
        email_tmpl_obj = self.env['mail.template']
        for each_cst in customers:
            attachment_id = each_cst.with_context({'mode':'auto'}).create_xls_consignment_report()
            email_tmpl_obj.send_mail(self, template_id, each_cst.id, True)
            #              send_mail(cr, uid, template.id, sched, True, context=context)
    """

#class mail_compose_message(models.Model):
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

    consignment_partner_id = fields.Many2one('res.partner','Report For', readonly=True)
    consignment_mode = fields.Selection([('auto','Automatic'),('manual','Manual')], string="Create Mode")
    
    @api.model
    def create(self, vals):
        attach = super(ir_attachment, self).create(vals)
        return attach
