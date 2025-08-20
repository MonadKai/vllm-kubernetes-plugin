
from vllm.core.block_manager import SelfAttnBlockSpaceManager
from vllm.sequence import SequenceStatus, SequenceGroup, Sequence
from vllm.v1.core.kv_cache_manager import KVCacheManager, KVCacheBlocks
from vllm.v1.request import Request, RequestStatus
import logging
from typing import Optional

from .common.logger_plugin import reset_logger_config


__all__ = ["patch_v0_allocate", "patch_v0_free", "patch_v1_allocate_slots", "patch_v1_free"]

logger = logging.getLogger(__name__)
reset_logger_config(logger)


def log_v0_allocate_result(self: SelfAttnBlockSpaceManager, seq_group: SequenceGroup) -> None:
    request_id = seq_group.request_id

    waiting_seqs = seq_group.get_seqs(status=SequenceStatus.WAITING)
    for seq in waiting_seqs:
        block_table = self.block_tables.get(seq.seq_id)
        if block_table:
            block_ids = [block.block_id for block in block_table._blocks]
            logger.info(f"[request_id={request_id}] allocated block for seq_id: {seq.seq_id} with block ids: {block_ids}")

    if seq_group.is_encoder_decoder():
        encoder_seq = seq_group.get_encoder_seq()
        if encoder_seq:
            block_table = self.block_tables.get(encoder_seq.seq_id)
            if block_table:
                block_ids = [block.block_id for block in block_table._blocks]
                logger.info(f"[request_id={request_id}] allocated block for encoder_seq_id: {encoder_seq.seq_id} with block ids: {block_ids}")


def log_v0_free_result(self: SelfAttnBlockSpaceManager, seq: Sequence) -> None:
    seq_id = seq.seq_id
    block_table = self.block_tables.get(seq.seq_id)
    if block_table:
        block_ids = [block.block_id for block in block_table._blocks]
        logger.info(f"freed block for seq_id={seq_id} with block ids: {block_ids}")


def patch_v0_allocate() -> None:
    old_allocate = SelfAttnBlockSpaceManager.allocate

    def patched_allocate(self: SelfAttnBlockSpaceManager, seq_group: SequenceGroup) -> None:
        old_allocate(seq_group)
        log_v0_allocate_result(self, seq_group)

    SelfAttnBlockSpaceManager.allocate = patched_allocate


def patch_v0_free() -> None:
    old_free = SelfAttnBlockSpaceManager.free

    def patched_free(self: SelfAttnBlockSpaceManager, seq: Sequence) -> None:
        old_free(seq)
        log_v0_free_result(self, seq)

    SelfAttnBlockSpaceManager.free = patched_free


def log_v1_allocate_slots_result(self: KVCacheManager, request: Request, result: Optional[KVCacheBlocks]) -> None:
    if result:
        block_ids = result.get_block_ids()
        logger.info(f"[request_id={request.request_id}] allocated block with block ids: {block_ids}")



def log_v1_free_result(self: KVCacheManager, request: Request) -> None:
    block_ids = self.get_block_ids(request.request_id)
    logger.info(f"[request_id={request.request_id}] freed block with block ids: {block_ids}")


def patch_v1_allocate_slots() -> None:
    old_allocate_slots = KVCacheManager.allocate_slots

    def patched_allocate_slots(self: KVCacheManager, request: Request, num_new_tokens: int, num_new_computed_tokens: int = 0, new_computed_blocks: Optional[KVCacheBlocks] = None, num_lookahead_tokens: int = 0, delay_cache_blocks: bool = False) -> Optional[KVCacheBlocks]:
        result = old_allocate_slots(request, num_new_tokens, num_new_computed_tokens, new_computed_blocks, num_lookahead_tokens, delay_cache_blocks)
        log_v1_allocate_slots_result(self, request, result)
        return result

    KVCacheManager.allocate_slots = patched_allocate_slots


def patch_v1_free() -> None:
    old_free = KVCacheManager.free

    def patched_free(self: KVCacheManager, request: Request) -> None:
        old_free(request)
        log_v1_free_result(self, request)

    KVCacheManager.free = patched_free
