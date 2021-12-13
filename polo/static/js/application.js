$(document).ready(function() {
     $("#sidebar").resizable({
       handleSelector: ".splitter",
       resizeHeight: false
     });

    var source_id;
    var faves_only = false;
    var debug = false;

    // these thresholds dictate coloring of the crystal score:
    //      RED < low_score_max < BLACK < high_score_min < GREEN
    var high_score_min = 0.6;
    var low_score_max = 0.2;

    /***********************************************************************************/
    var rockmaker_firsttime = true;
    var rockmaker_dropdown = $('#rockmaker_dropdown').dropdown({
        dataSource: '/api/sources/',
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
        dataBound: function(e) {
            if (localStorage.getItem("source_id")) {
                source_id = Number(localStorage.getItem("source_id"));
            } else {
                source_id = 1;
            }
            rockmaker_dropdown.value(source_id);
            rockmaker_firsttime = false;
        },
        change: function(e) {
            if (!rockmaker_firsttime) {
                source_id = rockmaker_dropdown.value();
                localStorage.setItem("source_id", source_id);
            }
            $('#search-text').val('');
            build_tree(source_id);
        }
    });

    /***********************************************************************************/
    var scorealgo_firsttime = true;
    var scorealgo_dropdown = $('#scorealgo_dropdown').dropdown({
        dataSource: '/api/algorithms/',
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
        dataBound: function(e) {
            var saved = localStorage.getItem("scorealgo");
            if (saved) {
                scorealgo_dropdown.value(saved);
            }
            algo_name = scorealgo_dropdown.value();
            scorealgo_firsttime = false;
        },
        change: function(e) {
            if (!scorealgo_firsttime) {
                algo_name = scorealgo_dropdown.value();
                localStorage.setItem("scorealgo", algo_name);
            }
        }
    });

    /***********************************************************************************/
    var scoretype_data = [
            { value: "date_imaged", text: "Most recent score", selected: true},
            { value: "crystal", text: "Highest score"},
        ];

    // load setting if present, and select saved value
    var scoretype = localStorage.getItem("scoretype");
    if (scoretype) {
        scoretype_data = scoretype_data.map(function(e) {
            if (e.value == scoretype) {
                e.selected = true;
            } else {
                delete e.selected;
            }
            return e;
        });
    }
    var scoretype_dropdown = $('#scoretype_dropdown').dropdown({
        dataSource: scoretype_data,
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
    });
    scoretype_dropdown.on('change', function(e) {
        localStorage.setItem("scoretype", scoretype_dropdown.value());
    })

    /***********************************************************************************/
    var numrows_data = [
            { value: "10", text: "10 (good for slow connections)"},
            { value: "30", text: "30"},
            { value: "100", text: "100", selected: true},
            { value: "300", text: "300"},
        ];

    // load setting if present, and select saved value
    var numrows = localStorage.getItem("numrows");
    if (numrows) {
        numrows_data = numrows_data.map(function(e) {
            if (e.value == numrows) {
                e.selected = true;
            } else {
                delete e.selected;
            }
            return e;
        });
    }
    var numrows_dropdown = $('#numrows_dropdown').dropdown({
        dataSource: numrows_data,
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
    });
    numrows_dropdown.on('change', function(e) {
        localStorage.setItem("numrows", numrows_dropdown.value());
    })

    /***********************************************************************************/
    var min_score_data = [
            { value: "0.8", text: "0.8 (most stringent)"},
            { value: "0.5", text: "0.5"},
            { value: "0.3", text: "0.1"},
            { value: "0.0", text: "0.0 (all scores)", selected: true},
        ];

    // load setting if present, and select saved value
    var min_score = localStorage.getItem("min_score");
    if (min_score) {
        min_score_data = min_score_data.map(function(e) {
            if (e.value == min_score) {
                e.selected = true;
            } else {
                delete e.selected;
            }
            return e;
        });
    }
    var min_score_dropdown = $('#min_score_dropdown').dropdown({
        dataSource: min_score_data,
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
    });
    min_score_dropdown.on('change', function(e) {
        localStorage.setItem("min_score", min_score_dropdown.value());
    })

    /***********************************************************************************/
    var scalebarsize_data = [
            { value: "200", text: "200 µm"},
            { value: "100", text: "100 µm", selected: true},
            { value: "50", text: "50 µm"},
        ];

    // load setting if present, and select saved value
    var scalebarsize = localStorage.getItem("scalebarsize");
    if (scalebarsize) {
        scalebarsize_data = scalebarsize_data.map(function(e) {
            if (e.value == scalebarsize) {
                e.selected = true;
            } else {
                delete e.selected;
            }
            return e;
        });
    }
    var scalebarsize_dropdown = $('#scalebarsize_dropdown').dropdown({
        dataSource: scalebarsize_data,
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
    });
    scalebarsize_dropdown.on('change', function(e) {
        localStorage.setItem("scalebarsize", scalebarsize_dropdown.value());
    })

    /***********************************************************************************/
    var showsparklines_data = [
            { value: "No", text: "No", selected: true},
            { value: "Yes", text: "Yes (slower to load)"},
        ];

    // load setting if present, and select saved value
    var showsparklines = localStorage.getItem("showsparklines");
    if (showsparklines) {
        showsparklines_data = showsparklines_data.map(function(e) {
            if (e.value == showsparklines) {
                e.selected = true;
            } else {
                delete e.selected;
            }
            return e;
        });
    }
    var showsparklines_dropdown = $('#showsparklines_dropdown').dropdown({
        dataSource: showsparklines_data,
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
    });
    showsparklines_dropdown.on('change', function(e) {
        localStorage.setItem("showsparklines", showsparklines_dropdown.value());
    })
    /***********************************************************************************/

    var tree = $('#tree').tree();
    var grid = $('#grid').grid();
    var timecourse_grid = $('#timecourse_grid').grid();
    var allimage_grid = $('#allimage_grid').grid();
    var faves = []; // to hold list of favorited grid rows

    // for debugging in browser
    $.exposed = {
        tree: tree,
        grid: grid,
        timecourse_grid,
        faves: faves,
        rockmaker_dropdown: rockmaker_dropdown,
        scorealgo_dropdown: scorealgo_dropdown,
        showsparklines_dropdown: showsparklines_dropdown
    }

    function highlight(e){
        $(e).addClass("highlight");
        setTimeout(function () {
              $(e).removeClass('highlight');
        }, 2000);
    }
    function setCurrentInfo(record) {
        return "Plate: <b>" + record.plate_name + "</b> " +
                "Protein: <b>" + record.protein + "</b> " +
                "Temperature: <b>" + record.temperature + '&deg;C' + "</b> " +
                // "Well/Drop: <b>" + record.well_name + '/' + record.drop_num + "</b> " +
                // "Crystal: <b>" + record.crystal + "</b> " +
                "Other: <b>" + record.other + "</b> " +
                "Date imaged: <b>" + record.date_imaged + "</b> " +
                (record.disputes ? "<span id=disputes>Manual: <b>" + record.disputes + '</span>': '') + "</b> " +
                "<br />Conditions: <b>" + record.conditions + "</b> ";
    }
    function massage_tree() {
        // this function takes the tree $('#tree') and overrides the selection mechanism with more useful behavior

        $('#tree span[data-role=display]').each(function(){
            // remove tree node selection event and replace with something more useful
            $(this).off("click");

            // selecting a node name is same as clicking the checkbox
            //$(this).on("click", function() {$(this).siblings("span[data-role=checkbox]").find("input").trigger("click")});

            // selecting a node name is same as clicking the expand/contract icon
            //$(this).on("click", function() {$(this).siblings("span[data-role=expander]").trigger("click")});

            // if not expandable, click checkbox. Otherwise click expander. Hopefully this behavior isn't too confusing.
            if ($(this).siblings("span[data-role=expander]").html() == "&nbsp;") {
                $(this).on("click", function() {$(this).siblings("span[data-role=checkbox]").find("input").trigger("click")});
            } else {
                $(this).on("click", function() {$(this).siblings("span[data-role=expander]").trigger("click")});
            }
        });
    }
    function search_tree() {
        $('#tree-overlay').show();
        $('#load_checked').hide();

        // set RockMaker instance
        source_id = rockmaker_dropdown.value();

        // get user query
        q = $('#search-text').val();
        if (debug) { console.log("Searching for: "+q) };

        if (typeof(tree) != "undefined") {
            tree.destroy();
        }

        if (typeof(folder) == "undefined" || folder == "None") {
            tree_data_source = '/api/search/?source_id='+source_id+'&q='+encodeURIComponent(q);
        } else {
            tree_data_source = '/api/search/?folder='+folder+'&source_id='+source_id+'&q='+encodeURIComponent(q);
        }

        tree = $('#tree').tree({
            primaryKey: 'id',
            dataSource: tree_data_source,
            lazyLoading: false,
            textField: 'name',
            hasChildrenField: 'has_children',
            checkboxes: true,
            uiLibrary: 'bootstrap',
            dataBinding: function(e) { $('#tree-overlay').show(); $('#load_checked').hide();},
            dataBound: function(e) {
                $('#tree-overlay').hide();
                if (debug) {console.log(tree.getAll())};
                if (tree.getAll().length > 0) {
                    $('#load_checked').show();
                    tree.expandAll();
                } else {
                    tree.html('<div class="alert alert-warning" role="alert">' +
                              '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
                              '  No matching plates, experiments, or proteins</div>');
                }
                massage_tree();
            }
        });

        tree.on('nodeDataBound', function (e, node, id, record) {
            if (record.node_type == 'ExperimentPlate') {
                node.attr('title', record.path);
                node.css('font-weight', "normal");
            } else if (record.node_type == 'Folder') {
                node.css('font-weight', "bold");
            }
        });
    }
    function build_tree(source_id) {
        $('#tree-overlay').show();
        $('#load_checked').hide();

        if (typeof(tree)  != "undefined") {
            tree.destroy();
        }

        if (typeof(source_id) == "undefined") {
            tree_data_source = '/api/tree/';
        } else if (typeof(folder) == "undefined" || folder == "None") {
            tree_data_source = '/api/tree/?source_id='+source_id;
        } else {
            tree_data_source = '/api/tree/?folder='+folder+'&source_id='+source_id;
        }

        tree = $('#tree').tree({
            primaryKey: 'id',
            dataSource: tree_data_source,
            lazyLoading: true,
            textField: 'name',
            hasChildrenField: 'has_children',
            checkboxes: true,
            uiLibrary: 'bootstrap',
            dataBinding: function(e) { $('#tree-overlay').show(); $('#load_checked').hide() },
            dataBound: function(e) { $('#tree-overlay').hide(); $('#load_checked').show(); massage_tree() }
        });

        tree.on('select', function(e, node, id) {
            if (tree.getCheckedNodes().some(n => n == id)) {
                tree.uncheck(node);
            } else {
                tree.check(node);
            }
        });

    }
    function load_plates() {
        var plates = tree.getCheckedNodes().filter(n => tree.getDataById(n).node_type == 'ExperimentPlate').map(i => tree.getDataById(i).plate_id);
        if (plates === undefined || plates.length == 0) {
            alert("Check at least one plate before loading");
            return false;
        }
        load_grid(plates);
    }
    function load_grid(plate_ids) {
        var method = scoretype_dropdown.value();
        var numrows = numrows_dropdown.value();
        var min_score = min_score_dropdown.value();
        var show_sparklines = showsparklines_dropdown.value();
        if (show_sparklines=="Yes") {
            var crystal_template = '<div class=bignum>{crystal}</div><span class="inlinesparkline" values="{all_crystal_scores}"></span>';
            var other_template = '<div class=bignum>{other}</div><span class="inlinesparkline" values="{all_other_scores}"></span>';
        } else {
            var crystal_template = '<div class=bignum>{crystal}</div>';
            var other_template = '<div class=bignum>{other}</div>';
        }

        faves = []; // clear favorites

        grid.destroy();
        grid = $('#grid').grid({
            dataSource: '/api/scores/?method=' + method +
                               '&source_id=' + source_id +
                               '&algo_name=' + encodeURIComponent(algo_name) +
                               '&plate_ids='+encodeURIComponent(plate_ids) +
                               '&min_score=' + min_score +
                               '&timecourse=' + (show_sparklines=="Yes"),
            selectionType: 'single',
            selectionMethod: 'basic',
            pager: { limit: numrows, sizes: [30, 100, 300] },
            uiLibrary: 'bootstrap',
            //fixedHeader: true,
            headerFilter: true,
            responsive: true,
            defaultColumnSettings: { align: 'center', sortable: true, filterable: false, priority: 1 },
            columns: [
                { field: 'favorite', title: '<span id="fave-header" class="glyphicon glyphicon-heart"></span>', width: 40, sortable: false },
                { field: 'plate_name', title: 'Plate', width: 145, cssClass: 'bignum' },
                { field: 'temperature', title: '&deg;C', width: 40, filterable: true, cssClass: 'bignum' },
                { field: 'well_name', title: 'Well', width: 70, cssClass: 'bignum' },
                { field: 'drop_num', title: 'Drop', width: 70, filterable: true, cssClass: 'bignum' },
                { field: 'crystal', title: 'Crystal', width: 70, tmpl: crystal_template },
                { field: 'other', title: 'Other', width: 70, tmpl: other_template },
                { field: 'url', title: 'Thumbnail', width: 130, sortable: false, tmpl: '<img oldsrc="{url}" src="{url}" width=120>'},
                { field: 'date_imaged', title: 'Date Imaged', width: 120, type: 'date' },
                { field: 'conditions', title: 'Conditions', align: 'left', sortable: false, priority: 2 },
                { field: 'protein', title: 'Protein', align: 'left', sortable: false, priority: 2 },
            ],
        });

        grid.on('dataBound', function(e, records, totalRecords) {
            if (debug) {console.log("grid dataBound")};
            records.forEach(function(data, i) {
                if (faves.includes(data.id)) {
                    data['favorite'] = '<span style="color: red;" class="polo-favorite glyphicon glyphicon-heart"></span>';
                    grid.updateRow(i+1, data);
                }
                //grid.find("tbody").css("height","100%") // make full height
            });

            // color-code crystal scores
            $('#grid tbody tr td:nth-child(6) div').each(function(i, ele) {
                $(this).removeClass('high-score medium-score low-score');
                if ($(this).text() > high_score_min ) {
                    $(this).addClass('high-score');
                } else if ($(this).text() < low_score_max ) {
                    $(this).addClass('low-score');
                } else {
                    $(this).addClass('medium-score');
                }
            });

            // add sparklines
            $.fn.sparkline.defaults.common.height = '20px';
            $.fn.sparkline.defaults.common.chartRangeMin = '0.0';
            $.fn.sparkline.defaults.common.chartRangeMax = '1.0';
            $.fn.sparkline.defaults.common.width = '50px';
            $.fn.sparkline.defaults.common.tooltipFormat = 'my-jqs-tooltip';

            $('.inlinesparkline').sparkline();

            $('#fave-header').off(); // turn off all eventlisteners on the header before adding one
            $('#fave-header').on('click tap', function() {
                if (debug) {console.log("#fave_header click or tap")};
                toggle_fave_view();
            });

        });
        grid.on('rowSelect', function (e, $row, id, record) {
            $('#current_image').attr("src", record.url);
            $('#current_image_well_drop').text(record.well_name + '/' + record.drop_num);
            $('#current_image_crystal_score').text(record.crystal);
            if (record.crystal >= high_score_min) {
                $('#current_image_crystal_score').css("color","green");
            } else if (record.crystal < low_score_max) {
                $('#current_image_crystal_score').css("color","red");
            } else {
                $('#current_image_crystal_score').css("color","black");
            }

            document.getElementById('current_info').innerHTML = setCurrentInfo(record);
            changeTab("tab-image");
            show_favorites();
        });
        changeTab("tab-list");
    };
    function previous_image() {
        var curr = grid.getSelected();
        if (curr != 1) {
            grid.setSelected(curr-1);
            show_favorites();
        }
    }
    function next_image() {
        var curr = grid.getSelected();
        if (curr == grid.count()) {
            alert("You're at the last loaded row ("+grid.count()+"). Go back to the list and load more rows. You can do this by scrolling all the way to the bottom of the list.");
        } else {
            // force loading of next image in case it had been paused.
            // Note that grid variable starts at index of 1, while the JS array starts at index of 0.
            $('#grid img')[curr].src = $('#grid img')[curr].getAttribute('oldsrc');
            grid.setSelected(curr+1);
            show_favorites();
        }
    }
    function toggle_favorite() {
        rownum = grid.getSelected();
        rowdata = grid.get(rownum);
        var i = faves.indexOf(rowdata.id);
        if ( i > -1) {
            // if row in selected, then remove from array and remove graphic from grid row
            faves.splice(i,1)
            rowdata['favorite'] = null;
            grid.updateRow(rownum, rowdata);
        } else {
            // otherwise add it to selected array and add graphic to grid row
            faves.push(rowdata.id)
            rowdata['favorite'] = '<span style="color: red;" class="polo-favorite glyphicon glyphicon-heart"></span>';
            grid.updateRow(rownum, rowdata);
        }
        grid.setSelected(rownum);
        show_favorites();
    }
    function show_favorites() {
        rownum = grid.getSelected();
        rowdata = grid.get(rownum);
        if (faves.indexOf(rowdata.id) > -1) {
            $('div#image div#favorite').show();
            $('#set-favorite span').addClass("favorite");
        } else {
            $('div#image div#favorite').hide();
            $('#set-favorite span').removeClass("favorite");
        }
    }
    function load_timecourse() {
        //changeTab("tab-timecourse");
        timecourse_grid.destroy();
        row = grid.get(grid.getSelected());
        if (typeof(row) == "undefined") {
          //alert("Load some plates and click an image first");
          document.getElementById('timecourse_info').innerHTML = '<div class="alert alert-warning" role="alert">Whoa there! Be sure to load some plates and click on a row before trying to get a timecourse.</div>';
          return false;
        }
        timecourse_grid = $('#timecourse_grid').grid({
            dataSource: '/api/timecourse/?source_id=' + source_id +
                        '&algo_name=' + encodeURIComponent(algo_name) +
                        '&plate_id=' + row.plate_id +
                        '&well_num=' + row.well_num +
                        '&drop_num=' + row.drop_num,
            selectionType: 'single',
            selectionMethod: 'basic',
            pager: { limit: 100, sizes: [30, 100, 300] },
            uiLibrary: 'bootstrap',
            //fixedHeader: true,
            defaultColumnSettings: { align: 'center', sortable: false, fontSize: '20px', tooltip: 'Click anywhere in row to open image in a new tab for close inspection' },
            columns: [
                { field: 'crystal', title: 'Crystal', width: 90, cssClass: 'bignum' },
                { field: 'other', title: 'Other', width: 90, cssClass: 'bignum' },
                { field: 'url', title: 'Thumbnail', width: 350, tmpl: '<img oldsrc="{url}" src="{url}" width=340>'},
                { field: 'date_imaged', title: 'Date Imaged', width: 120, type: 'date' }
            ],
        });
        document.getElementById('timecourse_info').innerHTML =
            "Plate: <b>" + row.plate_name +
            "</b>     Protein: <b>" + row.protein +
            "</b>     Temperature: <b>" + row.temperature + '&deg;C' +
            "</b>     Well/Drop: <b>" + row.well_name + '/' + row.drop_num +
            "</b>     Crystal: <b>" + row.crystal +
            "</b>     Other: <b>" + row.other +
            "</b>     Date imaged: <b>" + row.date_imaged +
            "</b><br />Conditions: <b>" + row.conditions + "</b>";

        timecourse_grid.on('rowSelect', function (e, $row, id, record) {
            var win = window.open(record.url, '_blank');
            win.focus();
        });

        timecourse_grid.on('dataBound', function(e, records, totalRecords) {

            // color-code crystal scores
            $('#timecourse_grid tbody tr td:nth-child(1) div').each(function(i, ele) {
                $(this).removeClass('high-score medium-score low-score');
                if ($(this).text() > high_score_min ) {
                    $(this).addClass('high-score');
                } else if ($(this).text() < low_score_max ) {
                    $(this).addClass('low-score');
                } else {
                    $(this).addClass('medium-score');
                }
            });
        });
    }
    function load_all() {
        //changeTab("tab-all");
        allimage_grid.destroy();
        row = grid.get(grid.getSelected());
        if (typeof(row) == "undefined") {
          //alert("Load some plates and click an image first");
          document.getElementById('all-image-types').innerHTML = '<div class="alert alert-warning" role="alert">Whoa there! Be sure to load some plates and click on a row first.</div>';
          return false;
        }
        allimage_grid = $('#allimage_grid').grid({
            dataSource: '/api/other/?source_id=' + source_id +
                        '&algo_name=' + encodeURIComponent(algo_name) +
                        '&plate_id=' + row.plate_id +
                        '&well_num=' + row.well_num +
                        '&drop_num=' + row.drop_num,
            selectionType: 'single',
            selectionMethod: 'basic',
            pager: { limit: 100, sizes: [30, 100, 300] },
            uiLibrary: 'bootstrap',
            //fixedHeader: true,
            defaultColumnSettings: { align: 'center', sortable: false, fontSize: '20px', tooltip: 'Click anywhere in row to open image in a new tab for close inspection' },
            columns: [
                { field: 'url', title: 'Thumbnail', width: 350, tmpl: '<div class=medium-image><img oldsrc="{url}" src="{url}" width=340><div class=image-info-bottom><span>{image_type}</span></div></div>'},
                { field: 'date_imaged', title: 'Date Imaged', width: 120, type: 'date' },
            ],
        });
        document.getElementById('all-image-types').innerHTML =
            "Plate: <b>" + row.plate_name +
            "</b>     Protein: <b>" + row.protein +
            "</b>     Temperature: <b>" + row.temperature + '&deg;C' +
            "</b>     Well/Drop: <b>" + row.well_name + '/' + row.drop_num +
            "</b><br />Conditions: <b>" + row.conditions + "</b>";

        allimage_grid.on('rowSelect', function (e, $row, id, record) {
            var win = window.open(record.url, '_blank');
            win.focus();
        });
    }
    function toggle_fave_view() {
        if (debug) {console.log("toggle_fave_view()")};
        fave_header = document.getElementById('fave-header');
        if (faves_only == false) {
            if (debug) {console.log("  show faves only")};
            faves_only = true;
            $(fave_header).addClass('only_faves');
            grid.reload({ scores: faves });
        } else {
            if (debug) {console.log("  show all ")};
            faves_only = false;
            $(fave_header).removeClass('only_faves');
            grid.reload( {scores: ''});
        }
    }
    function dispute(manual_call) {
        $.post( "/api/dispute/",
                {
                  image_score_id: grid.get(grid.getSelected()).id,
                  disputed_by: auth_username,
                  manual_call: manual_call
                },
                function(data, status, jqXHR) {
                    // success
                    if (debug) { console.log(data) };

                    // add manual call to disputes string
                    record = grid.get(grid.getSelected());
                    if (record.disputes == null) {
                        record.disputes = manual_call;
                    } else {
                        record.disputes = record.disputes + "," + manual_call;
                    }

                    // show new disputes and highlight
                    $('#current_info').html(setCurrentInfo(record));
                    highlight($('span#disputes')); // since not using jQueryUI
                })
                .fail(function() {
                    alert("Error saving the manual annotation");
                });
    }

    $('#search-plates-form').on('submit', function() { search_tree(); return false; }); // by returning false, suppress reloading of page
    $('#search-button').on('click tap', function() { search_tree(); return false; }); // by returning false, suppress reloading of page
    $('#load_checked').on('click tap', function() { load_plates() });
    $('#clear-search-button').on('click tap', function() {
        $('#search-text').val('');
        build_tree(rockmaker_dropdown.value());
    });
    $('#download_grid').on('click tap', function() {
        // convert favorites to something more excel-friendly...
        grid.getAll().forEach(function(data, i) {
                if (data['favorite'] == '<span style="color: red;" class="polo-favorite glyphicon glyphicon-heart"></span>') {
                    data['favorite'] = "Favorite";
                    grid.updateRow(i+1, data);
                }
        });

        grid.downloadCSV('polo.csv', true);

        // ...and back again
        grid.getAll().forEach(function(data, i) {
                if (data['favorite'] == "Favorite") {
                    data['favorite'] = '<span style="color: red;" class="polo-favorite glyphicon glyphicon-heart"></span>';
                    grid.updateRow(i+1, data);
                }
        });
    });
    $('div#image_navigation div#up').on('click tap', function() { previous_image() });
    $('div#image_navigation div#down').on('click tap', function() { next_image() });
    $('div#image_navigation div#set-favorite').on('click tap', function() { toggle_favorite() });
    $('#restore-settings').on('click tap', function() {
        if (confirm("This will restore settings and reload the page. Continue?")) {
            localStorage.clear();
            location.reload();
        }
    });

    // SCALEBAR LOGIC
    // draggable without the need for JQueryUI via https://stackoverflow.com/questions/2424191/how-do-i-make-an-element-draggable-in-jquery
    // rotating element inspired from https://jsfiddle.net/o5jjosvu/65/

    function get_degrees(e, mouse_x, mouse_y) {
        var radius = e.outerWidth() / 2;
        var center_x = e.offset().left + radius;
        var center_y = e.offset().top + radius;
        var radians = Math.atan2(mouse_x - center_x, mouse_y - center_y);
        var degrees = Math.round((radians * (180 / Math.PI) * -1) + 100);
        return degrees;
    }

    function handle_mousedown(e){
        if (e.ctrlKey) {
            // rotate
            var scalebar = $(this);
            // Calculate the mouse position in degrees
            var click_degrees = get_degrees(scalebar, e.pageX, e.pageY);
            $(document).bind('mousemove', click_degrees, function(event) {
                // Calculate the mouse move position, removing starting point
                var degrees = get_degrees(scalebar, event.pageX, event.pageY) - click_degrees;
                scalebar.css('transform', 'rotate('+degrees+'deg)');
            });
            $(document).on('mouseup', function() {
                $(document).unbind('mousemove');
            });
        } else {
            // translate
            window.my_dragging = {};
            my_dragging.pageX0 = e.pageX;
            my_dragging.pageY0 = e.pageY;
            my_dragging.elem = this;
            my_dragging.offset0 = $(this).offset();
            function handle_dragging(e){
                var left = my_dragging.offset0.left + (e.pageX - my_dragging.pageX0);
                var top = my_dragging.offset0.top + (e.pageY - my_dragging.pageY0);
                $(my_dragging.elem).offset({top: top, left: left});
            }
            function handle_mouseup(e){
                $('body')
                .off('mousemove', handle_dragging)
                .off('mouseup', handle_mouseup);
            }
            $('body')
            .on('mouseup', handle_mouseup)
            .on('mousemove', handle_dragging);
        }
    }

    function update_scalebar() {
        // TODO: if the image does not change, there is no need to go to the network
        var i = $('#current_image');
        try {
            var url_re = RegExp('batchID_(\\d+).*profileID_(\\d+).*d\\d_r(\\d+)_');
            var m = url_re.exec(i.attr('src'));
            var batch_id=m[1];
            var profile_id=m[2];
            var region_id=m[3];
        } catch(err) {
            console.log("ERROR getting image information for scalebar")
            return
        }

        $.get('/api/image_info/?source_id='+source_id+'&batch_id='+batch_id+'&profile_id='+profile_id+'&region_id='+region_id)
            .done(function(data) {
                var pixel_size = data.pixel_size;
                var bar_length = scalebarsize_dropdown.value();
                var w = (Number(bar_length)/Number(pixel_size))*(i[0].clientWidth/i[0].naturalWidth);
                $('#scalebar').width(w);
                $('#bar-legend').html(bar_length + " &micro;m");
                $('#scalebar').show();
                var left_pos=i[0].clientWidth-Math.max($('#scalebar').width(),50)-10;
                $('#scalebar').css({left: left_pos+'px', top: '', bottom: '25px'});
                $('#scalebar').css('transform','rotate(0deg)');
            })
            .fail(function() {
                console.log("error getting pixel size");
                $('#scalebar').hide();
            });
    }

    // KEYBOARD SHORTCUTS
    var Key = {
      LEFT:   37,
      UP:     38,
      RIGHT:  39,
      DOWN:   40,
      HOME:   36,
      END:    35,
      SPACE:  32,
      H:      72,   // help
      F:      70,   // toggle showing favorites
      D:      68,   // dispute
      C:      67,   // dispute: clear
      P:      80,   // dispute: precipitate
      X:      88,   // dispute: crystal
      O:      79,   // dispute: other
      S:      83,   // dispute: salt (or other false positive)
    };
    function _addEventListener(evt, element, fn) {
      if (window.addEventListener) {
        element.addEventListener(evt, fn, false);
      }
      else {
        element.attachEvent('on'+evt, fn);
      }
    }
    function handleKeyboardEvent(evt) {
      if (!evt) {evt = window.event;} // for old IE compatible
      var keycode = evt.keyCode || evt.which; // also for cross-browser compatible
      if (document.activeElement.tagName == 'INPUT') {return false}; // ignore when typing in a text box

      switch (keycode) {
        case Key.LEFT:
            if (currentTabName() == 'tab-all') {
                load_timecourse();
                changeTab("tab-timecourse");
            } else if (currentTabName() == 'tab-timecourse') {
                changeTab("tab-image");
            } else if (currentTabName() == 'tab-image') {
                changeTab("tab-list");
                var rows = $('#grid tr');
                if (grid.getSelected()) {
                    rows[grid.getSelected()].scrollIntoView();
                } else {
                    rows[1].scrollIntoView();
                }
            } else if (currentTabName() == 'tab-list') {
                changeTab("tab-help");
            }
            break;
        case Key.RIGHT:
            if (currentTabName() == 'tab-help') {
                changeTab("tab-list");
                var rows = $('#grid tr');
                if (grid.getSelected()) {
                    rows[grid.getSelected()].scrollIntoView();
                } else {
                    rows[1].scrollIntoView();
                }
            } else if (currentTabName() == 'tab-list') {
                changeTab("tab-image");
            } else if (currentTabName() == 'tab-image') {
                load_timecourse();
                changeTab("tab-timecourse");
            } else if (currentTabName() == 'tab-timecourse') {
                load_all();
                changeTab("tab-all");
            }
            break;
        case Key.UP:
          if (currentTabName() == 'tab-image') {
            previous_image();
          }
          break;
        case Key.DOWN:
          if (currentTabName() == 'tab-image') {
            next_image();
          }
          break;
        case Key.HOME:
          if (currentTabName() == 'tab-image') {
            grid.setSelected(1);
            update_scalebar();
            show_favorites();
          }
          break;
        case Key.END:
          if (currentTabName() == 'tab-image') {
            grid.setSelected(grid.count());
            update_scalebar();
            show_favorites();
          }
          break;
        case Key.SPACE:
          if (currentTabName() == 'tab-image') {
            toggle_favorite();
          }
          break;
        case Key.F:
          toggle_fave_view();
          break;
        case Key.H:
          changeTab("tab-help");
          break;
        case Key.D:
          if (currentTabName() == 'tab-image') {
            dispute("D");
          }
          break;
        case Key.C:
          if (currentTabName() == 'tab-image') {
            dispute("C");
          }
          break;
        case Key.P:
          if (currentTabName() == 'tab-image') {
            dispute("P");
          }
          break;
        case Key.X:
          if (currentTabName() == 'tab-image') {
            dispute("X");
          }
          break;
        case Key.O:
          if (currentTabName() == 'tab-image') {
            dispute("O");
          }
          break;
        case Key.S:
          if (currentTabName() == 'tab-image') {
            dispute("S");
          }
          break;

        default:
          break;
      }
    }
    _addEventListener('keydown', document, handleKeyboardEvent);

    // for tabs - inspired by https://catalin.red/css3-jquery-folder-tabs/
    function currentTabName() { return $('#tabs > li#current > a').attr("name") };
    function changeTab(target) {
        $("#content").find("[id^='tab']").hide(); // Hide all content
        $("#tabs > li").attr("id",""); //Reset id's
        $('#tabs > li > a[name='+target+']').parent().attr("id","current"); // Activate this
        $('#' + target).show(); // Show content for the current tab

        // disable image loading on inactive tabs
        if (target == 'tab-list') {
          $('#grid img').each(function() {this.src = this.getAttribute('oldsrc')});

          // disable images in other grids to avoid unnecessary downloads
          $('#timecourse_grid img').each(function() {this.src = ''});
          $('#allimage_grid img').each(function() {this.src = ''});

          var rows = $('#grid tr');
          if (grid.getSelected()) {
            rows[grid.getSelected()].scrollIntoView();
          } else {
            rows[1].scrollIntoView();
          }
        } else if (target == 'tab-image') {
            update_scalebar();
            // disable images loading in all grids
            $('#grid img').each(function() {this.src = ''});
            $('#timecourse_grid img').each(function() {this.src = ''});
            $('#allimage_grid img').each(function() {this.src = ''});
        } else if (target == 'tab-timecourse') {
            load_timecourse();
            // reenable all images in timecourse_grid
            $('#timecourse_grid img').each(function() {this.src = this.getAttribute('oldsrc')});

            // disable all images in other grids to avoid unnecessary downloads of a potentially long list of images
            $('#grid img').each(function() {this.src = ''});
            $('#allimage_grid img').each(function() {this.src = ''});
        } else if (target == 'tab-all') {
            load_all();
            // reenable all images in allimage_grid
            $('#allimage_grid img').each(function() {this.src = this.getAttribute('oldsrc')});

            // disable all images in other grids to avoid unnecessary downloads of a potentially long list of images
            $('#grid img').each(function() {this.src = ''});
            $('#timecourse_grid img').each(function() {this.src = this.getAttribute('oldsrc')});
        }
    }
    $('#tabs a').on('click tap', function(e) {
        e.preventDefault();
        target = $(this).attr('name');
        if ($(this).closest("li").attr("id") == "current"){ //detection for current tab
            return;
        }
        else{
            changeTab(target);
        }
    });

    $(window).resize(function(){
        update_scalebar();
    });

    // start on help tab
    changeTab("tab-help");
    $('#scalebar').mousedown(handle_mousedown); // make scalebar draggable
    $('#scalebar').hide();

    // if source and plate(s) specified in URL, load them
    if (typeof(plate_ids) != "undefined" && plate_ids != "None" && typeof(load_source) != "undefined" && load_source != "None") {
        source_id = load_source;
        load_grid(plate_ids);
    }
});
