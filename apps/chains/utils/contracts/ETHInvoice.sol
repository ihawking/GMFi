// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ETHInvoice {
    constructor(address _to) {
        payable(_to).transfer(address(this).balance);
    }
}