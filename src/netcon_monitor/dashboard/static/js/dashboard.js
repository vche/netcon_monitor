function set_refresh(period_sec) {
    clearInterval(refreshTimer);
    $(".refresh_nav").each(function() {$(this).removeClass("active")});
    $("#refresh-" + period_sec).addClass("active");
    if (period_sec > 0) refreshTimer = setInterval(refreshDashboards, period_sec*1000);
}

function refreshDashboards() {
    console.log(new Date(Date.now()).toISOString() + ": Requesting dashboard data");
    // $.get(getDashboardsDatatUrl, function(data) {dataReceived(data);});
}

// function dataReceived(json_resp)
// {
//     console.log(new Date(Date.now()).toISOString() + ": Received dashboard data");

//     // Update tables
//     dt = $("#db-card-table-" + json_resp.dashboards[i].db_id).DataTable();
//     dt.clear(); // TODO: only send new elements, then don't clear
//     dt.rows.add(json_resp.dashboards[i].table_data)
//     dt.draw()
//     }
//     $("#last_update").html("Last updated: " + new Date(Date.now()).toLocaleTimeString())
//     $('#loadsign').hide();
//     console.log(new Date(Date.now()).toISOString() + ": Processed dashboard data");
// }


function formatFloatTime(ftime) {
    if (ftime < 1) return `${ftime * 1000} ms`;
    if (ftime < 60) return `${ftime.toFixed(3)} s`;
    time_str = ""
    rem = ftime
    if (ftime > 3600) {
        hours = Math.floor(ftime/3600)
        time_str += hours + " h ";
        rem = ftime - hours*3600;
    }
    mins = Math.floor(rem/60);
    secs = rem - mins*60;
    time_str += `${mins} min ${secs.toFixed(3)} s`;
    return time_str;
}

function createDashboardTable(tableId, ctxt = false, tab_data=null)
{
  // Custom filter to display or not the row with online value = False
  $.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
      if ( settings.nTable.id == tableId ) {
        var episodes = parseFloat( data[7] ) || 0; // use data for the episodes column
        if ((data[7] == "False") && !$("#show_offline").prop( "checked" )) return false;
      }
      return true;
    }
  );

  var dbTable = $('#'+tableId).DataTable( {
    // "columns": [{ "width": 25 },{  }],
    // "initComplete": function( settings, json ) {},
    data: tab_data,
    columnDefs: [
      {
          targets: "datetime_column",
          render: $.fn.dataTable.render.moment("YYYY-MM-DD HH:mm:ss.SSSS", "YYYY/MM/DD HH:mm:ss"),
      },
      {
          targets: "hidden_column",
          visible: false,
      },
    ],
    "pageLength": 20,
    "responsive": true,
    "dom": datatable_dom(),
    "buttons": datatable_buttons(),
    "order": [[ 1, "desc" ]]
  } );

  // Add click listener to refresh the tabel if the show empty input is changed
  $("#show_offline").on('click', function () {
    dbTable.draw();
  } );

  return dbTable
}

function datatable_dom()
{
  // Style buttons top left, filter top right, rows/page bottom left, showed and pages bottom right
  return  "<'row db-hdr' <'custom-dt-btn col-sm-4 col-md-6'B> <'col-sm-6 col-md-6'f>  >" +
          "<'row' <'col-sm-12 'tr> >" +
          "<'row db-hdr' <'col-sm-12 col-md-4'l> <'col-sm-12 col-md-4'i><'col-sm-12 col-md-4'p>>"
}

function datatable_buttons()
{
  // Define col button menu with col selection, and export button menu with exports
  return [
    {
      extend: 'colvis',
      collectionLayout: 'two-column',
      text: "Hide columns",
      className: "db-hdr-dropdown",
      prefixButtons: [
        {
          extend: 'colvisGroup',
          text: 'Show all',
          show: ':hidden'
        },
        {
          extend: 'colvisRestore',
          text: 'Restore'
        }
      ]
    },
    {
      extend: 'collection',
      text: 'Export',
      buttons: [
        {
          text: 'Copy',
          extend: 'copyHtml5',
          footer: false,
          exportOptions: { columns: ':visible' }
        },
        {
          text: 'CSV',
          extend: 'csvHtml5',
          fieldSeparator: ';',
          exportOptions: { columns: ':visible' }
        },
        {
          text: 'Print',
          extend: 'print',
          fieldSeparator: ';',
          exportOptions: { columns: ':visible' }
        },
     ]
    }
  ]
}

function allow_device(key)
{    
    if ($("#allow-" + key)[0].checked == true) { $.get("/allow/" + key, function(data) {dataReceived(key, data);}); }
    else { $.get("/disallow/" + key, function(data) {dataReceived(key, data);}); }
}
  
function dataReceived(key, json_resp)
{
    $("#allow-" + key).prop( "checked", json_resp.status)
    if (json_resp.status) { $("#dev-" + key).removeClass("dev_alarm"); }

}

// Page start, to execute when the page is fully loaded
function pageStart()
{
    // Show the loader, hide the dashboards; and request the data
    $('#loadsign').show();

    // Create the datatables of each dashboard
    createDashboardTable('connection-table');

    // Request dashboards data
    refreshDashboards();
}
