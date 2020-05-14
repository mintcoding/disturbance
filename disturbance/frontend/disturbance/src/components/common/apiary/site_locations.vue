<template lang="html">

    <div class="row" style="padding-bottom: 50px;">
        <div>
            <div v-if="is_external">
                <h3>Application: {{ proposal.lodgement_number }}</h3>
                <h4>Application Type: {{proposal.proposal_type }}</h4>
                <h4>Status: {{proposal.customer_status }}</h4>
            </div>

            <div class="col-md-12">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Site Locations<small></small>
                            <a class="panelClicker" :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                                <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                            </a>
                        </h3>
                    </div>

                    <div class="panel-body collapse in" :id="pBody">
                        <span class="col-sm-12">
                            <!--
                            <TextField 
                            -->
                            <input
                                type="text" 
                                v-model="proposal.apiary_site_location.title" 
                                :readonly="is_internal || !proposal.can_user_edit" 
                            />
                        </span>
                        <span class="col-sm-12">
                            Mark the location of the new proposed site either by entering the latitude and longitude or by clicking the location in the map.
                        </span>
                        <div class="row col-sm-12">
                            <div class="col-sm-4 form-group">
                                <label class="inline">Latitude:</label>
                                <div v-if="true">
                                    <input 
                                        type="number" 
                                        min="-90" 
                                        max="90" 
                                        class="form-control" 
                                        v-model.number="proposal.apiary_site_location.latitude" 
                                        :readonly="is_internal || !proposal.can_user_edit" 
                                    />
                                </div>
                            </div>
                        </div>
                        <div class="row col-sm-12">
                            <div class="col-sm-4 form-group">
                                <label class="inline">Longitude:</label>
                                <div v-if="true">
                                    <input 
                                        type="number" 
                                        min="-180" 
                                        max="180" 
                                        class="form-control" 
                                        v-model.number="proposal.apiary_site_location.longitude" 
                                        :readonly="is_internal || !proposal.can_user_edit" 
                                    />
                                    <input type="button" @click="addProposedSite" value="Add proposed site" class="btn btn-primary">
                                </div>
                            </div>
                        </div>

                        <div class="row col-sm-12">
                            <datatable ref="site_locations_table" id="site-locations-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" />
                        </div>

                        <iframe width="500" height="500" :src="webmap_src"></iframe>
                            <!--
                        <IFrame width="500" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" title="Apiary Sites Beekeeper's Map (WBV)" :src="webmap_src"></IFrame>
                            -->

                        <div class="col-sm-12">
                            <label>
                                Click <a @click="enlargeMapClicked">here</a> to enlarge map
                            </label>
                        </div>
                        <div class="col-sm-12">
                            <label>
                                Click <a @click="existingSiteAvailableClicked">here</a> if you are interested in existing sites that are available by the site licence holder.
                            </label>
                        </div>
                    </div>
                </div>

                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Deed Poll<small></small>
                        <a class="panelClicker" href="#deedPoll" data-toggle="collapse"  data-parent="#userInfo" expanded="true" aria-controls="deedPoll">
                        <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                        </h3>
                    </div>
                    <div class="panel-body collapse in" id="deedPoll">
                        <div class="row">
                            <div class="col-sm-12">
                                <label>Print <a :href="deed_poll_url" target="_blank">the deed poll</a>, sign it, have it witnessed and attach it to this application.</label>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm-12">
                                <FileField :proposal_id="proposal.id" :isRepeatable="false" name="deed_poll" :id="'proposal'+proposal.id" :readonly="proposal.readonly" ref="deed_poll_doc"></FileField>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Checklist<small></small>
                        <a class="panelClicker" href="#checkList" data-toggle="collapse"  data-parent="#userInfo" expanded="true" aria-controls="checkList">
                          <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                        </h3>
                    </div>
                    <div class="panel-body collapse in" id="checkList">
                        <div v-if="q" class="row">
                            <div class="col-sm-12">
                                <li class="col-sm-6" >
                                    <label class="control-label">{{q.question.text}}</label>
                                </li>
                                <ul v-if="q.question.answer_type=='yes_no'" class="list-inline col-sm-6">
                                    <li class="list-inline-item">
                                        <input  class="form-check-input" v-model="q.answer" ref="Checkbox" type="radio" :name="'option'+q.id" :id="'answer_one'+q.id":value="true" data-parsley-required :disabled="readonly"/> Yes
                                    </li>
                                    <li class="list-inline-item">
                                        <input  class="form-check-input" v-model="q.answer" ref="Checkbox" type="radio" :name="'option'+q.id" :id="'answer_two'+q.id" :value="false" data-parsley-required :disabled="readonly"/> No 
                                    </li>
                                </ul>
                                <ul v-else class="list-inline col-sm-6">
                                    <li class="list-inline-item">
                                        <textarea :disabled="readonly" class="form-control" name="text_answer" placeholder="" v-model="q.text_answer"></textarea>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <SiteLocationsModal ref="site_locations_modal" />
    </div>
</template>

<script>

    import TextField from '@/components/forms/text.vue'
    import FileField from '@/components/forms/filefield.vue'
    import datatable from '@vue-utils/datatable.vue'
    import uuid from 'uuid';
    import SiteLocationsModal from './site_locations_modal';

    export default {
        props:{
            proposal:{
                type: Object,
                required:true
            },
            canEditActivities:{
              type: Boolean,
              default: true
            },
            is_external:{
              type: Boolean,
              default: false
            },
            is_internal:{
              type: Boolean,
              default: false
            },
            is_referral:{
              type: Boolean,
              default: false
            },
            hasReferralMode:{
                type:Boolean,
                default: false
            },
            hasAssessorMode:{
                type:Boolean,
                default: false
            },
            referral:{
                type: Object,
                required:false
            },
            proposal_parks:{
                type:Object,
                default:null
            },
        },
        data:function () {
            let vm=this;
            return{
                q: null,
                values:null,
                pBody: 'pBody'+vm._uid,
                webmap_src: 'https://dpaw.maps.arcgis.com/apps/Embed/index.html?webmap=1d956bc5513e40568a4f01950906b64b&extent=95.5777,-38.2527,149.5425,-12.3581&home=true&zoom=true&scale=true&search=true&searchextent=true&details=true&disable_scroll=true&theme=light',
                showingHelpText: false,
                help_text: 'My Help text ...',
                marker_lng: null,
                marker_lat: null,
                site_locations: [],
                deed_poll_url: '',
                dtHeaders: [
                    'id',
                    'guid',
                    'Latitude',
                    'Longitude',
                    'Action',
                ],
                dtOptions: {
                    serverSide: false,
                    searchDelay: 1000,
                    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                    order: [
                        [0, 'desc']
                    ],
                    language: {
                        processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                    },
                    responsive: true,
                    processing: true,
                    columns: [
                        {
                            mRender: function (data, type, full) {
                                if (full.id) {
                                    return full.id;
                                } else {
                                    return '';
                                }
                            }
                        },
                        {
                            mRender: function (data, type, full) {
                                if (full.site_guid) {
                                    return full.site_guid;
                                } else {
                                    return '';
                                }
                            }
                        },
                        {
                            mRender: function (data, type, full) {
                                return full.latitude;
                            }
                        },
                        {
                            mRender: function (data, type, full) {
                                return full.longitude;
                            }
                        },
                        {
                            mRender: function (data, type, full) {
                                let ret_str = '<span class="delete_button" style="color:#347ab7; cursor: pointer;" data-site-location-guid="' + full.site_guid + '">Delete</span>';
                                return ret_str;
                            }
                        },
                    ],
                },
            }
        },
        components: {
            TextField,
            FileField,
            datatable,
            SiteLocationsModal,
        },
        computed:{

        },
        watch:{

        },
        methods:{
            enlargeMapClicked: function() {
                console.log('enlargeMapClicked');
                this.$nextTick(() => {
                    this.$refs.site_locations_modal.isModalOpen = true;
                });
            },
            existingSiteAvailableClicked: function() {
                console.log('existingSiteAvailableClicked');
                alert("TODO: open screen 45: External - Contact Holder of Available Site in a different tab page.");
            },
            constructSiteLocationsTable: function(){
                // Clear table
                this.$refs.site_locations_table.vmDataTable.clear().draw();

                // Construct table
                if (this.site_locations.length > 0){
                    for(let i=0; i<this.site_locations.length; i++){
                        this.addSiteLocationToTable(this.site_locations[i]);
                    }
                }
            },
            addSiteLocationToTable: function(site_location){
                console.log('*** addSiteLocationToTable ***');
                console.log(site_location);
                this.$refs.site_locations_table.vmDataTable.row.add(site_location).draw();
            },
            addProposedSite: function(){
                console.log('addProposedSite');
                this.site_locations.push({
                    "id": '',
                    "latitude": this.proposal.apiary_site_location.latitude,
                    "longitude": this.proposal.apiary_site_location.longitude,
                    "site_guid": uuid()
                });
                this.constructSiteLocationsTable();
            },
            addEventListeners: function(){
                $("#site-locations-table").on("click", ".delete_button", this.removeSiteLocation);
            },
            removeSiteLocation: function(e){
                let site_location_guid = e.target.getAttribute("data-site-location-guid");
                console.log('guid');
                console.log(site_location_guid);

                for (let i=0; i<this.site_locations.length; i++){
                    if (this.site_locations[i].site_guid == site_location_guid){
                        this.site_locations.splice(i, 1);
                    }
                }
                this.constructSiteLocationsTable();
            },
        },
        mounted: function() {
            let vm = this;
            this.$nextTick(() => {
                vm.addEventListeners();
            });
            for(let i=0; i<this.proposal.apiary_site_location.apiary_sites.length; i++){
                let a_site = this.proposal.apiary_site_location.apiary_sites[i];
                a_site.longitude = 'retrieve from GIS server'
                a_site.latitude = 'retrieve from GIS server'
                this.site_locations.push(a_site);
            }
            this.constructSiteLocationsTable();
        }
    }
</script>

<style lang="css" scoped>
    .delete_button {
        color: #337ab7 !important;
    }
    .section{
        text-transform: capitalize;
    }
    .list-group{
        margin-bottom: 0;
    }
    .fixed-top{
        position: fixed;
        top:56px;
    }
</style>
