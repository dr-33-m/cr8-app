import { toast } from "sonner";

export function createPeerConnection(): RTCPeerConnection {
  const config: RTCConfiguration = {
    iceServers: [
      {
        urls: "stun:stun.l.google.com:19302",
      },
    ],
  };
  return new RTCPeerConnection(config);
}

export function handleTrackEvent(
  event: RTCTrackEvent,
  videoElement: HTMLVideoElement | null
) {
  if (!videoElement) {
    console.error("No video element available");
    return;
  }

  if (event.streams[0]) {
    videoElement.srcObject = event.streams[0];
    videoElement.play().catch((error) => {
      console.error("Error playing video:", error);
      toast.error("Failed to play video stream");
    });
  }
}

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

export async function handleAnswer(
  peerConnection: RTCPeerConnection,
  answer: RTCSessionDescriptionInit
) {
  try {
    await peerConnection.setRemoteDescription(
      new RTCSessionDescription(answer)
    );
  } catch (error) {
    console.error("Error setting remote description:", error);
    toast.error("Failed to establish WebRTC connection");
    throw error;
  }
}

export async function handleIncomingICECandidate(
  peerConnection: RTCPeerConnection,
  candidate: RTCIceCandidateInit
) {
  try {
    await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
  } catch (error) {
    console.error("Error adding ICE candidate:", error);
    toast.error("Failed to establish peer connection");
    throw error;
  }
}

export async function createAndSendOffer(
  peerConnection: RTCPeerConnection,
  sendSignal: (signal: any) => void
) {
  try {
    const offer = await peerConnection.createOffer({
      offerToReceiveVideo: true,
      offerToReceiveAudio: false,
    });

    await peerConnection.setLocalDescription(offer);

    sendSignal({
      command: "webrtc",
      signalType: "offer",
      signalData: {
        sdp: peerConnection.localDescription?.sdp,
        type: peerConnection.localDescription?.type,
      },
    });
  } catch (error) {
    console.error("Error creating offer:", error);
    toast.error("Failed to initialize WebRTC connection");
    throw error;
  }
}
