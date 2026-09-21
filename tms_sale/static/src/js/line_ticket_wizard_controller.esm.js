import { usePlugin } from "@odoo/owl";
import {formView} from "@web/views/form/form_view";
import {registry} from "@web/core/registry";
import { ActionManagerPlugin } from "@web/webclient/actions/action_plugin";

export class TicketConfiguratorController extends formView.Controller {
    setup() {
        super.setup();
        this.action = usePlugin(ActionManagerPlugin);
    }

    async onRecordSaved(record) {
        await super.onRecordSaved(...arguments);
        const {trip_id, ticket_ids} = record.data;
        return this.action.doAction({
            type: "ir.actions.act_window_close",
            infos: {
                ticketConfiguration: {
                    tms_trip_ticket_id: trip_id,
                    tms_ticket_ids: ticket_ids.currentIds,
                },
            },
        });
    }
}

registry.category("views").add("sale_order_line_seat_ticket_form", {
    ...formView,
    Controller: TicketConfiguratorController,
});
