import { CesiumInitializer, ExternalCommsUtils, InternalCommsUtils } from "./utils/comms_utils.jsm";

window.dash_clientside = Object.assign({}, window.dash_clientside, {
   Cesium: {
      startup_cesium: async function(id, config) {

         const configJSON = JSON.parse(config);
         const token = configJSON["cesium_token"];
         const localServer = configJSON["local_server"];

         CesiumInitializer.token = token;
         CesiumInitializer.localServer = localServer;
         CesiumInitializer.ID = id;

         return await CesiumInitializer.viewer_initializer();
      },

      external_transmissions: function(data, cesium_viewer) {

         cesium_viewer.dataSources.removeAll();
         cesium_viewer.entities.removeAll();

         const jsonData = JSON.parse(data);
         for (const group in jsonData) {
            const transmission = jsonData[group]["transmission"];
            const info = jsonData[group]["info"];
            const line_data = jsonData[group]["line_points"];
            const current_time = jsonData[group]["current_time"];
            
            let transmission_info = ExternalCommsUtils.transmissionText(transmission, current_time, info);
            ExternalCommsUtils.createPoints(info, transmission_info, cesium_viewer);
            ExternalCommsUtils.createLine(line_data, transmission_info, cesium_viewer);
         }
      },

      internal_transmissions: function(data, cesium_viewer) {

         const jsonData = JSON.parse(data);
         for (const platform in jsonData) {
            const info = jsonData[platform]["info"];
            const current_time = jsonData[platform]["current_time"];
            
            let transmission_info = InternalCommsUtils.internalTransmissionText(platform, current_time, info);
            InternalCommsUtils.createPoint(info, transmission_info, cesium_viewer);
         }
      },

      track_contributions: function(data, cesium_viewer) {

         const jsonData = JSON.parse(data);
         for (const owningPlatform in jsonData)
         {
            const platformLocation = jsonData[owningPlatform].Location;
            const currentTime = jsonData[owningPlatform].CurrentTime;
            const masterTrackList = jsonData[owningPlatform].LocalTracks;
            for (const localTrack in masterTrackList)
            {
               const contributorList = masterTrackList[localTrack].Contributors;
               for (const contributor in contributorList)
               {
                  const contributorLine = contributorList[contributor].Line;
                  const x = contributorLine.x;
                  const y = contributorLine.y;
                  const z = contributorLine.z;
                  for (let i = 0; i < x.length - 1; i++) {
                     try {
                        cesium_viewer.entities.add({
                           polyline: {
                              positions: [
                                 new Cesium.Cartesian3(x[i], y[i], z[i]), 
                                 new Cesium.Cartesian3(x[i+1], y[i+1], z[i+1])],
                              width: 20,
                              material: new Cesium.PolylineArrowMaterialProperty(Cesium.Color.SNOW)
                           },
                           description: "TRACK INFO" 
                        });
                     }
                     catch (error) {
                        console.log(error);
                     }
                  }
               }
            }
            console.log("PARSED");
         }
      },

      camera_view: function(camera_location, cesium_viewer) {

         const jsonCamera = JSON.parse(camera_location);
         let adjustCamera = function(camera_location, cesium_viewer) {

            cesium_viewer.camera.flyTo({
               destination: new Cesium.Cartesian3(
                  camera_location.x, 
                  camera_location.y, 
                  camera_location.z),
               duration: 1
            });
         }

         adjustCamera(jsonCamera, cesium_viewer);
      }
   }
});