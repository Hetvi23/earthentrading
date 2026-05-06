/** Lead + Earth Trading extensions (mirror custom fields). */

export type EtLeadLine = {
	name?: string;
	owner?: string;
	creation?: string;
	modified?: string;
	parent?: string;
	parentfield?: string;
	parenttype?: string;
	doctype?: string;
	docstatus?: number;
	idx?: number;
	item_code?: string;
	qty?: number;
	uom?: string;
	commodity?: string;
};

export type LeadDoc = {
	name?: string;
	doctype?: string;
	docstatus?: number;
	lead_name?: string;
	company_name?: string;
	status?: string;
	email_id?: string;
	phone?: string;
	mobile_no?: string;
	source?: string;
	lead_owner?: string;
	custom_et_sales_stage?: string;
	custom_et_assigned_trader?: string;
	custom_et_region?: string;
	custom_et_deal_type?: string;
	custom_et_incoterm?: string;
	custom_et_lines?: EtLeadLine[];
};

export type OpportunityDoc = {
	name?: string;
	doctype?: string;
	party_name?: string;
	customer_name?: string;
	opportunity_from?: string;
	status?: string;
	opportunity_owner?: string;
	custom_et_assigned_trader?: string;
	custom_et_deal_type?: string;
	items?: Record<string, unknown>[];
	title?: string;
};
