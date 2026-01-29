export const CesiumInitializer = {

   assetID: "2",
   ID: null,
   token: null,
   localServer: null,
   checkToken : async function () {
      try
      {
         const response = await fetch(`https://api.cesium.com/v1/assets/${this.assetID}/endpoint`, 
            {
               method: 'GET',
               headers: {
                  'Authorization': `Bearer ${this.token}`
               }
            }
         );

         return response.status;
      }
      catch (error) {

         return error.message;
      }
   },

   viewer_initializer : async function () {

      const response = await this.checkToken();

      if (response === 200)
      {
         Cesium.Ion.defaultAccessToken = this.token; 
      }

      const viewer = new Cesium.Viewer(this.ID, 
         {
            baseLayerPicker: false,
            geocoder: false,
            fullscreenButton: false,
            timeline: false,
            sceneModePicker: false,
            animation: false,
         }
      );

      if (response === "Failed to fetch" || response === 401)
      {
         const world_jpg = `${this.localServer}world`;
         const imageryLayer = new Cesium.ImageryLayer(
            new Cesium.SingleTileImageryProvider({
               url: world_jpg
            })
         );
         viewer.imageryLayers.add(imageryLayer);
      }

      EventListeners.setPointHoverEvent(viewer);
      EventListeners.setArrowHoverEvent(viewer);

      return viewer;
   }
}

const EventListeners = {
   setArrowHoverEvent : function (viewer)
      {
         const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas); 
         let pickedEntity = null; // Store the currently picked entity

         handler.setInputAction(function (movement) {
            const pick = viewer.scene.pick(movement.endPosition);

            if (Cesium.defined(pick) && Cesium.defined(pick.id) && pick.id.polyline !== undefined && pick.id !== pickedEntity) {

               pickedEntity = pick.id;

               // Display description
               const tooltip = document.getElementById('tooltip'); 
               tooltip.style.left = movement.endPosition.x + 'px'; 
               tooltip.style.top = movement.endPosition.y + 'px'; 
               tooltip.style.display = 'block'; 
               tooltip.innerHTML = pickedEntity.description; 
            } else if (!Cesium.defined(pick) && pickedEntity) {
               // Mouse moved away from the entity
               pickedEntity = null; 

               // Hide description
               const tooltip = document.getElementById('tooltip'); 
               tooltip.style.display = 'none'; 
            }
         }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
      },

   setPointHoverEvent : function (viewer)
   {
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas); 
      let pickedEntity = null; // Store the currently picked entity
      let oldColor = null; // Store the original color of the picked entity


      handler.setInputAction(function (movement) {
         const pick = viewer.scene.pick(movement.endPosition);

         if (Cesium.defined(pick) && Cesium.defined(pick.id) && pick.id.point !== undefined && pick.id !== pickedEntity) {

            // New entity hovered
            if (pickedEntity) {
               // Restore color of previously hovered entity
               pickedEntity.point.color = oldColor;
            }

            pickedEntity = pick.id;
            oldColor = pickedEntity.point.color.getValue(); 
            pickedEntity.point.color = Cesium.Color.YELLOW; 

            // Display description
            const tooltip = document.getElementById('tooltip'); 
            tooltip.style.left = movement.endPosition.x + 'px'; 
            tooltip.style.top = movement.endPosition.y + 'px'; 
            tooltip.style.display = 'block'; 
            tooltip.innerHTML = pickedEntity.description; 
         } else if (!Cesium.defined(pick) && pickedEntity) {
            // Mouse moved away from the entity
            pickedEntity.point.color = oldColor; // Restore original color
            pickedEntity = null; 

            // Hide description
            const tooltip = document.getElementById('tooltip'); 
            tooltip.style.display = 'none'; 
         }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
   }
}

export const ExternalCommsUtils = {
   transmission_color : {
      SUCCESS : Cesium.Color.AQUAMARINE,
      FAIL : Cesium.Color.DARKRED
   },

   createPoints : function(info, transmission_info, cesium_viewer) {
      const indices = Object.keys(info["Sender_Name"]);

      const sender_name = info["Sender_Name"][indices[0]];
      const sender_X = info["SenderLocation_X"][indices[0]];
      const sender_Y = info["SenderLocation_Y"][indices[0]];
      const sender_Z = info["SenderLocation_Z"][indices[0]];
      const sender_position = new Cesium.Cartesian3(sender_X, sender_Y, sender_Z);

      const receiver_name = info["Receiver_Name"][indices[0]];
      const receiver_X = info["ReceiverLocation_X"][indices[0]];
      const receiver_Y = info["ReceiverLocation_Y"][indices[0]];
      const receiver_Z = info["ReceiverLocation_Z"][indices[0]];
      const receiver_position = new Cesium.Cartesian3(receiver_X, receiver_Y, receiver_Z);

      try {
         cesium_viewer.entities.add({
            position: sender_position,
            point: {
               pixelSize: 10,
               color: transmission_info["color"],
            },
            id: sender_name,
            description: transmission_info["transmission_info"]
         });
      }
      catch (error) {
         console.log(`EXTERNAL COMMS Sender: ${error.message}`);
      }

      try {
         cesium_viewer.entities.add({
            position: receiver_position,
            point: {
               pixelSize: 10,
               color: transmission_info["color"],
            },
            id: receiver_name,
            description: transmission_info["transmission_info"]
         });
      }
      catch (error) {
         console.log(`EXTERNAL COMMS Receiver: ${error.message}`);
      }
   },

   createLine : function(line_data, transmission_info, cesium_viewer) {

      let x = line_data["x"];
      let y = line_data["y"];
      let z = line_data["z"];
      for (let i = 0; i < x.length - 1; i++) {
         try {
            cesium_viewer.entities.add({
               polyline: {
                  positions: [
                     new Cesium.Cartesian3(x[i], y[i], z[i]), 
                     new Cesium.Cartesian3(x[i+1], y[i+1], z[i+1])],
                  width: 20,
                  material: new Cesium.PolylineArrowMaterialProperty(transmission_info["color"])
               },
               description: transmission_info["transmission_info"]
            });
         }
         catch (error) {
            console.log(error);
         }
      }
   },

   transmissionText : function(transmission, info)
   {

      const indices = Object.keys(info["Sender_Name"]);
      const [sender, sender_part, receiver, receiver_part] = transmission

      let transmission_result = "SUCCESS";
      let transmission_num = 0;
      let transmission_info = '';
      for (let i = 0; i < indices.length; i++)
      {
         transmission_num += 1;
         transmission_info += `
         <b>${transmission_num}. Event Type: ${info["Event_Type"][indices[i]]}</b><br>
         &nbsp;&nbsp;&nbsp;&nbsp;<b>Sender: ${sender} >> Receiver: ${receiver}</b><br>
         &nbsp;&nbsp;&nbsp;&nbsp;Simulation Time: ${info["SimulationTime"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Platform Parts: ${sender_part} >> ${receiver_part}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Type: ${info["Message_Type"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Number: ${info["Message_SerialNumber"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Originator: ${info["Message_Originator"][indices[i]]}<br>`
         if (info["CommInteraction_FailedStatus"][indices[i]] !== "Does Not Exist")
         {
            transmission_info += `&nbsp;&nbsp;&nbsp;&nbsp;Failure Reason: ${info["CommInteraction_FailedStatus"][indices[i]]}<br>`;
            transmission_result = "FAIL" ;
         }
      }

      const result = {
         "transmission_info": transmission_info, 
         "color": this.transmission_color[transmission_result]
      };

      return result;
   }
}

export const InternalCommsUtils = {

   createPoint : function(info, transmission_info, cesium_viewer) {
      const indices = Object.keys(info["Sender_Name"]);

      const sender_name = info["Sender_Name"][indices[0]];
      const sender_X = info["SenderLocation_X"][indices[0]];
      const sender_Y = info["SenderLocation_Y"][indices[0]];
      const sender_Z = info["SenderLocation_Z"][indices[0]];
      const sender_position = new Cesium.Cartesian3(sender_X, sender_Y, sender_Z);

      let entity = cesium_viewer.entities.getById(sender_name);
      if (entity === undefined)
      {
         cesium_viewer.entities.add({
            position: sender_position,
            point: {
               pixelSize: 10,
               color: Cesium.Color.LIGHTCORAL,
            },
            id: sender_name,
            description: transmission_info
         });

      }
      else // entity already exists
      {
         console.log("ADDING INTERNAL COMMS INFO...");
         entity.description._value += '<br>' + transmission_info;
         entity.point.color = Cesium.Color.LEMONCHIFFON;
      }
   },

   internalTransmissionText : function(platform, info)
   {         
      const indices = Object.keys(info["Sender_Name"]);

      let transmission_num = 0;
      let transmission_info = '';
      for (let i = 0; i < indices.length; i++)
      {
         transmission_num += 1;
         transmission_info += `
         <b>${transmission_num}. Event Type: ${info["Event_Type"][indices[i]]}</b><br>
         &nbsp;&nbsp;&nbsp;&nbsp;<b>Platform: ${platform}</b><br> 
         &nbsp;&nbsp;&nbsp;&nbsp;Simulation Time: ${info["SimulationTime"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Platform Parts: ${info["SenderPart_Name"][indices[i]]} >> ${info["ReceiverPart_Name"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Type: ${info["Message_Type"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Number: ${info["Message_SerialNumber"][indices[i]]}<br>
         &nbsp;&nbsp;&nbsp;&nbsp;Message Originator: ${info["Message_Originator"][indices[i]]}<br>`
      }

      return transmission_info;
   }
}