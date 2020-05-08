$( document ).ready(function() {
    var source_id;
    var algo_name;
    var faves_only = false;
    var debug = false;

    var high_score_min = 0.6;
    var low_score_max = 0.2;

    var rockmaker_dropdown = $('#rockmaker_dropdown').dropdown({
        dataSource: '/api/sources/',
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
        change: function(e) {
            source_id = e.target.options[e.target.selectedIndex].value;
            $('#search-text').val('');
            build_tree(source_id);
        }
    });

    var scorealgo_dropdown = $('#scorealgo_dropdown').dropdown({
        dataSource: '/api/algorithms/',
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome',
        change: function(e) {
            algo_name = e.target.options[e.target.selectedIndex].value;
        }
    });

    var scoretype_dropdown = $('#scoretype_dropdown').dropdown({
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome'
    });

    var numrows_dropdown = $('#numrows_dropdown').dropdown({
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome'
    });

    var min_score_dropdown = $('#min_score_dropdown').dropdown({
        valueField: 'id',
        textField: 'name',
        uiLibrary: 'bootstrap',
        iconsLibrary: 'fontawesome'
    });

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
        rockmaker_dropdown: rockmaker_dropdown
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
        e = document.getElementById('rockmaker_dropdown');
        source_id = e.options[e.selectedIndex].value;

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

        if (typeof(folder) == "undefined" || folder == "None") {
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
        load_grid(tree.getCheckedNodes().filter(n => tree.getDataById(n).node_type == 'ExperimentPlate').map(i => tree.getDataById(i).plate_id));
    }
    function load_grid(plate_ids) {
        //var plate_ids = tree.getCheckedNodes().filter(n => tree.getDataById(n).node_type == 'ExperimentPlate').map(i => tree.getDataById(i).plate_id)
        var sel1 = document.getElementById('scoretype_dropdown');
        var method = sel1.options[sel1.selectedIndex].value;
        var sel2 = document.getElementById('numrows_dropdown');
        var numrows = sel2.options[sel2.selectedIndex].value;
        var sel3 = document.getElementById('min_score_dropdown');
        var min_score = sel3.options[sel3.selectedIndex].value;

        faves = []; // clear favorites

        grid.destroy();
        grid = $('#grid').grid({
            dataSource: '/api/scores/?method=' + method +
                               '&source_id=' + source_id +
                               '&algo_name=' + encodeURIComponent(algo_name) +
                               '&plate_ids='+encodeURIComponent(plate_ids) +
                               '&min_score=' + min_score,
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
                { field: 'crystal', title: 'Crystal', width: 70, tmpl: '<div class=bignum>{crystal}</div><span class="inlinesparkline" values="{all_crystal_scores}"></span>' },
                { field: 'other', title: 'Other', width: 70, tmpl: '<div class=bignum>{other}</div><span class="inlinesparkline" values="{all_other_scores}"></span>' },
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
        e = document.getElementById('rockmaker_dropdown');
        build_tree(e.options[e.selectedIndex].value);
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
            show_favorites();
          }
          break;
        case Key.END:
          if (currentTabName() == 'tab-image') {
            grid.setSelected(grid.count());
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
        } else {
            // disable images loading in all grids
            $('#grid img').each(function() {this.src = ''});
            $('#timecourse_grid img').each(function() {this.src = ''});
            $('#allimage_grid img').each(function() {this.src = ''});
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

    // start on help tab
    changeTab("tab-help");

    // if source and plate(s) specified in URL, load them
    if (typeof(plate_ids) != "undefined" && plate_ids != "None" && typeof(load_source) != "undefined" && load_source != "None") {
        source_id = load_source;
        load_grid(plate_ids);
    }

});
