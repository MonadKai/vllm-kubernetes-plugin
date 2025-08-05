from typing import List
from pydantic import BaseModel


class PackageScannedInfo(BaseModel):
    package_name: str
    package_version: str
    modules_with_logger: List[str]
    methods_with_request_id: List[str]
