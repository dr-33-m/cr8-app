import adapter from "webrtc-adapter";

// Initialize WebRTC adapter
console.log(
  `WebRTC adapter initialized: ${adapter.browserDetails.browser} ${adapter.browserDetails.version}`
);

// WebRTC configuration
export const rtcConfig = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" },
    // Add TURN servers here if needed
  ],
  iceCandidatePoolSize: 10,
};

// Media constraints for receiving video
export const mediaConstraints = {
  video: true,
  audio: false,
};

// Helper function to create a new RTCPeerConnection
export function createPeerConnection(): RTCPeerConnection {
  const pc = new RTCPeerConnection(rtcConfig);

  // Log state changes
  pc.oniceconnectionstatechange = () => {
    console.log(`ICE connection state: ${pc.iceConnectionState}`);
  };

  pc.onconnectionstatechange = () => {
    console.log(`Connection state: ${pc.connectionState}`);
  };

  pc.onsignalingstatechange = () => {
    console.log(`Signaling state: ${pc.signalingState}`);
  };

  return pc;
}

// Helper function to handle ICE candidate events
export function handleICECandidateEvent(
  event: RTCPeerConnectionIceEvent,
  sendSignal: (signal: any) => void
) {
  if (event.candidate) {
    sendSignal({
      command: "webrtc",
      signalType: "ice-candidate",
      signalData: {
        candidate: event.candidate.candidate,
        sdpMid: event.candidate.sdpMid,
        sdpMLineIndex: event.candidate.sdpMLineIndex,
      },
    });
  }
}

// Helper function to handle incoming tracks
export function handleTrackEvent(
  event: RTCTrackEvent,
  videoElement: HTMLVideoElement | null
) {
  if (videoElement && event.streams[0]) {
    videoElement.srcObject = event.streams[0];
  }
}

// Helper function to create and send an offer
export async function createAndSendOffer(
  pc: RTCPeerConnection,
  sendSignal: (signal: any) => void
) {
  try {
    const offer = await pc.createOffer({
      offerToReceiveVideo: true,
      offerToReceiveAudio: false,
    });

    await pc.setLocalDescription(offer);

    sendSignal({
      command: "webrtc",
      signalType: "offer",
      signalData: {
        sdp: pc.localDescription?.sdp,
        type: pc.localDescription?.type,
      },
    });
  } catch (error) {
    console.error("Error creating offer:", error);
    throw error;
  }
}

// Helper function to handle incoming answers
export async function handleAnswer(
  pc: RTCPeerConnection,
  answer: RTCSessionDescriptionInit
) {
  try {
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
  } catch (error) {
    console.error("Error setting remote description:", error);
    throw error;
  }
}

// Helper function to handle incoming ICE candidates
export async function handleIncomingICECandidate(
  pc: RTCPeerConnection,
  candidate: RTCIceCandidateInit
) {
  try {
    await pc.addIceCandidate(new RTCIceCandidate(candidate));
  } catch (error) {
    console.error("Error adding ICE candidate:", error);
    throw error;
  }
}
