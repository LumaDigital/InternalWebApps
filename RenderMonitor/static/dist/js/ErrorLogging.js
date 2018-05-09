        function displayStats() {
            var logTextDiv = document.getElementById('logText');
            var logText = logTextDiv.textContent;

            // Split error log lines in into array
            var lines = logText.split(", ");

            // Find error lines and string handling
            for(var i = 0;i < lines.length;i++) {
               if(lines[i].includes("JobState.error")) {
                   var jobType = getJobType(lines[i]);
                   var jobDiv = jobType.toString().toLowerCase();
                   document.getElementById(jobDiv).innerText = jobType;

                   // Get divs and set up content containers
                   var farmDivName = "farms_" + jobDiv;
                   var farmName = lines[i].match(/O(.*)J/);
                   var divText = extractDivText(farmDivName);
                   var div = document.createElement("div");
                   div.setAttribute("id", farmName[1]);
                   var farmDiv = document.getElementById(farmDivName);

                   // Check if the farm is already listed
                   // if not add it, else increase the error count
                   if(!divText.includes(farmName[1])) {
                       div.innerHTML = " " + farmName[1] + "\t1 ";
                       document.getElementById(farmDivName).appendChild(div);
                   } else {
                       var farmElements = document.getElementById(farmName[1]);
                       farmElements.parentNode.removeChild(farmElements);
                       var splitDiv = divText.split(" ");
                       splitDiv.splice(0, 1); // Remove leading white space
                       for(var k=0; k < splitDiv.length; k++) {
                            if(farmName[1].includes(splitDiv[k]) && splitDiv[k].charCodeAt(0) > 57) {
                                var errorCount = parseInt(splitDiv[k+1]);
                                splitDiv[k + 1] = errorCount + 1;
                                div.innerHTML = "  " + splitDiv[k] + " \t" + splitDiv[k + 1] + " ";
                            }
                       }
                       farmDiv.appendChild(div);
                   }
               }
           }
        }

        function extractDivText(elemID) {
            var t = document.getElementById(elemID).textContent;
            return t;
        }

        function getJobType(errorLine) {
            var jobType = "";

            if(errorLine.includes("\\AnimationRecordingOutput")) {
                jobType = errorLine.match(/Animation/);
            } else if(errorLine.includes("\\CompositingOutput")) {
                jobType = errorLine.match(/Compositing/);
            } else if(errorLine.includes("\\PreviewFrameRenderingOutput")) {
                jobType = errorLine.match(/Preview/);
            } else if(errorLine.includes("\\RenderingOutput")) {
                jobType = errorLine.match(/Rendering/);
            } else if(errorLine.includes("\\SplitRenderingOutput")) {
                jobType = errorLine.match(/Split/);
            } else if(errorLine.includes("\\VideoOutput")) {
                jobType = errorLine.match(/Video/);
            }
            return jobType;
        }