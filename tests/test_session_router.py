import pytest
import os
from gamma_runtime.session_router import SessionRouter, ModelLane, PlayerProfile

def test_router_topology():
    run_root = "test_run"
    router = SessionRouter(run_root)
    
    # Register lanes
    gemma_lane = ModelLane(
        lane_id="office_mac_gemma_player_lane",
        role="scientific_worker",
        host="100.69.184.42",
        canonical_model_id="gemma-4-e4b-it-mlx"
    )
    gptoss_lane = ModelLane(
        lane_id="office_mac_gptoss_judge_lane",
        role="judge_critic",
        host="100.69.184.42",
        canonical_model_id="gpt-oss-20b"
    )
    
    router.register_lane(gemma_lane)
    router.register_lane(gptoss_lane)
    
    # Register profiles
    for i in range(1, 9):
        router.register_profile(PlayerProfile(
            player_profile_id=f"office_mac_gemma_player_{i:02}",
            role="scientific_worker",
            lane_id="office_mac_gemma_player_lane",
            canonical_model_id="gemma-4-e4b-it-mlx"
        ))
        router.register_profile(PlayerProfile(
            player_profile_id=f"office_mac_gptoss_judge_{i:02}",
            role="judge_critic",
            lane_id="office_mac_gptoss_judge_lane",
            canonical_model_id="gpt-oss-20b"
        ))
        
    assert len(router.profiles) == 16
    
    # Bind sessions
    for i in range(1, 9):
        binding = router.bind_session(
            session_id=f"gemma_session_{i:02}",
            player_profile_id=f"office_mac_gemma_player_{i:02}",
            harness_id=f"harness_{i:02}"
        )
        assert binding.canonical_model_id == "gemma-4-e4b-it-mlx"
        assert binding.lane_id == "office_mac_gemma_player_lane"
        assert "gemma_session" in binding.transcript_path
        
    for i in range(1, 9):
        binding = router.bind_session(
            session_id=f"gptoss_session_{i:02}",
            player_profile_id=f"office_mac_gptoss_judge_{i:02}",
            harness_id=f"harness_{i+8:02}"
        )
        assert binding.canonical_model_id == "gpt-oss-20b"
        assert binding.lane_id == "office_mac_gptoss_judge_lane"

def test_model_id_validation():
    router = SessionRouter("test_run")
    
    # Rejection of suffix
    with pytest.raises(ValueError, match="cannot contain runtime suffix"):
        router.register_lane(ModelLane(
            lane_id="bad_lane",
            role="tester",
            host="localhost",
            canonical_model_id="gemma-4-e4b-it-mlx:2"
        ))
        
    # Rejection of quarantined
    with pytest.raises(ValueError, match="is quarantined"):
        router.register_lane(ModelLane(
            lane_id="quarantined_lane",
            role="tester",
            host="localhost",
            canonical_model_id="gemma-4-e4b-it-mxfp8"
        ))

def test_lms_request_model():
    router = SessionRouter("test_run")
    router.register_lane(ModelLane(
        lane_id="lane1", role="role1", host="host1", canonical_model_id="model1"
    ))
    router.register_profile(PlayerProfile(
        player_profile_id="profile1", role="role1", lane_id="lane1", canonical_model_id="model1"
    ))
    router.bind_session("session1", "profile1", "harness1")
    
    assert router.get_lms_request_model("session1") == "model1"

def test_truth_mode_preservation():
    router = SessionRouter("test_run")
    router.register_lane(ModelLane(
        lane_id="lane1", role="role1", host="host1", canonical_model_id="model1",
        truth_mode="truth_safe_unverified"
    ))
    router.register_profile(PlayerProfile(
        player_profile_id="profile1", role="role1", lane_id="lane1", canonical_model_id="model1",
        truth_mode="truth_safe_unverified",
        truth_bearing_run=False
    ))
    binding = router.bind_session("session1", "profile1", "harness1")
    assert binding.truth_mode == "truth_safe_unverified"
    assert binding.truth_bearing_run is False

def test_standard_topology():
    router = SessionRouter.create_office_mac_standard_topology("office_run")
    assert len(router.lanes) == 2
    assert len(router.profiles) == 16
    assert "office_mac_gemma_player_01" in router.profiles
    assert "office_mac_gptoss_judge_08" in router.profiles
